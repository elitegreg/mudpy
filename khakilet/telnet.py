from .socket import socket

__all__ = ['LineTooLong', 'ConnectionClosed', 'InputStream']

class LineTooLong(IOError): pass
class ConnectionClosed(IOError): pass

class Interrupt(IOError): pass

class Term(IOError):
    def __init__(self, term):
      self.term = term

class WindowSize(IOError):
    def __init__(self, x=80, y=24):
        self.x = x
        self.y = y


class TelnetStream(socket):
    buffer_size = 1024

    def __init__(self, socket):
        self._rawq = b''
        self._cookedq = b''
        self.eof = 0
        self.iacseq = b'' # Buffer for IAC sequence.
        self.sb = 0 # flag for SB and SE sequence.
        self.sbdataq = b''

        if hasattr(socket, 'recv'):
            self.recvfun = socket.recv
        elif hasattr(socket, 'read'):
            self.recvfun = socket.read
        elif hasattr(socket, '__call__'):
            self.recvfun = socket
        else:
            raise NotImplemenetedError()

    def readline(self, endline=b'\n', maxlen=1024):
        """Reads a line from a socket

        Line returned includes endline string. If connection closed on a
        half-line ``ConnectionClosed`` is raised. 
        """
        suflen = len(endline)
        while True:
            idx = self._buf.find(endline)
            if idx >= 0:
                idx += suflen
                res = self._buf[:idx]
                self._buf = self._buf[idx:]
                return res
            oldlen = len(self._buf)
            if maxlen <= oldlen:
                raise LineTooLong()
            chunk = self.recvfun(self.buffer_size)
            if not chunk:
                raise ConnectionClosed()
            self._buf += chunk

    def __fill_queue(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.

        """
        buf = [b'', b'']
        try:
            while self.rawq:
                c = self.rawq_getchar()
                if not self.iacseq:
                    if c == theNULL:
                        continue
                    if c == b"\021":
                        continue
                    if c != IAC:
                        buf[self.sb] = buf[self.sb] + c
                        continue
                    else:
                        self.iacseq += c
                elif len(self.iacseq) == 1:
                    # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
                    if c in (DO, DONT, WILL, WONT):
                        self.iacseq += c
                        continue

                    self.iacseq = b''
                    if c == IAC:
                        buf[self.sb] = buf[self.sb] + c
                    else:
                        if c == SB: # SB ... SE start.
                            self.sb = 1
                            self.sbdataq = b''
                        elif c == SE:
                            self.sb = 0
                            self.sbdataq = self.sbdataq + buf[1]
                            buf[1] = b''
                        if self.option_callback:
                            # Callback is supposed to look into
                            # the sbdataq
                            self.option_callback(self.sock, c, NOOPT)
                        else:
                            # We can't offer automatic processing of
                            # suboptions. Alas, we should not get any
                            # unless we did a WILL/DO before.
                            self.msg('IAC %d not recognized' % ord(c))
                elif len(self.iacseq) == 2:
                    cmd = self.iacseq[1:2]
                    self.iacseq = b''
                    opt = c
                    if cmd in (DO, DONT):
                        self.msg('IAC %s %d',
                            cmd == DO and 'DO' or 'DONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(IAC + WONT + opt)
                    elif cmd in (WILL, WONT):
                        self.msg('IAC %s %d',
                            cmd == WILL and 'WILL' or 'WONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(IAC + DONT + opt)
        except EOFError: # raised by self.rawq_getchar()
            self.iacseq = b'' # Reset on EOF
            self.sb = 0
            pass
        self.cookedq = self.cookedq + buf[0]
        self.sbdataq = self.sbdataq + buf[1]
