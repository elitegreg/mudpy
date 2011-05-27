from .socket import socket

from telnetlib import AO, AYT, BRK, DM, DO, DONT, ECHO, IAC, IP, LINEMODE, NAWS, SB, SGA, SE, TTYPE, TM, WILL, WONT, theNULL

__all__ = ['LineTooLong', 'ConnectionClosed', 'InputStream']

class LineTooLong(IOError): pass
class ConnectionClosed(IOError): pass

class Interrupt(IOError): pass

class TerminalType(IOError):
    def __init__(self, term):
      self.term = term

class WindowSize(IOError):
    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height


class TelnetResponses:
  TELNET_BREAK_RESPONSE = IAC + WILL + TM
  TELNET_IP_RESPONSE    = IAC + WILL + TM
  TELNET_ABORT_RESPONSE = IAC + DM
  TELNET_DO_TM_RESPONSE = IAC + WILL + TM
  TELNET_DO_NAWS        = IAC + DO + NAWS
  TELNET_DO_TTYPE       = IAC + DO + TTYPE
  TELNET_TERM_QUERY     = IAC + SB + TTYPE + bytes([1]) + IAC + SE
  TELNET_WONT_ECHO      = IAC + WONT + ECHO
  TELNET_WILL_ECHO      = IAC + WILL + ECHO
  TELNET_WILL_SGA       = IAC + WILL + SGA
  TELNET_AYT_RESPONSE   = '\n[-Yes-]\n'
  TELNET_DONT_LINEMODE  = IAC + DONT + LINEMODE



class TelnetStream:
    buffer_size = 1024

    def __init__(self, socket):
        self.__socket = socket
        self.__rawq = b''
        self.__dataq = [b'', b'']
        self.__iacseq = b''
        self.__sb = 0

    def __getattr__(self, attr):
      return getattr(self.__socket, attr)

    def readline(self, endline=b'\n', maxlen=1024):
        """Reads a line from a socket

        Line returned includes endline string. If connection closed on a
        half-line ``ConnectionClosed`` is raised. 
        """
        suflen = len(endline)

        while True:
            idx = self.__dataq[0].find(endline)
            if idx >= 0:
                idx += suflen
                res = self.__dataq[0][:idx]
                self.__dataq[0] = self.__dataq[0][idx:]
                return res
            oldlen = len(self.__dataq[0])
            if maxlen <= oldlen:
                raise LineTooLong()
            self.__fill_queue()

    def __fill_queue(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.

        """

        if not self.__rawq:
            self.__rawq = self.__socket.recv(self.buffer_size)
            if not self.__rawq:
                raise ConnectionClosed()

        try:
          for (i, c) in enumerate(self.__rawq):
              c = bytes([c])
              if not self.__iacseq:
                  if c not in (IAC, theNULL, b"\021"):
                      self.__dataq[self.__sb] += c
                  else:
                      if c == IAC:
                          self.__iacseq += c
                      continue
              elif len(self.__iacseq) == 1:
                  # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
                  if c in (DO, DONT, WILL, WONT):
                      self.__iacseq += c
                      continue

                  self.__iacseq = b''
                  if c == IAC:
                      self.__dataq[self.__sb] += c
                  else:
                      if c == SB: # SB ... SE start.
                          self.__sb = 1
                          self.__dataq[self.__sb] = b''
                      elif c == SE:
                          self.__sb = 0
                      self.__handle_option(c, self.__dataq[1])
              elif len(self.__iacseq) == 2:
                  cmd = self.__iacseq[1:2]
                  self.__iacseq = b''
                  if cmd in (DO, DONT):
                      self.__handle_option(cmd, c)
                  elif cmd in (WILL, WONT):
                      self.__handle_option(cmd, c)
        finally:
            self.__rawq = self.__rawq[i+1:]

    def __handle_option(self, cmd, opt):
        print('__handle_option: %s, %s' % (cmd, opt))
        if cmd == BRK:
            self.send(TelnetResponses.TELNET_BREAK_RESPONSE)
        elif cmd == IP:
            self.send(TelnetResponses.TELNET_IP_RESPONSE)
            raise Interrupt()
        elif cmd == AYT:
            self.send(TelnetResponses.TELNET_AYT_RESPONSE)
        elif cmd == AO:
            self.sock.send(TelnetResponses.TELNET_ABORT_RESPONSE,
                socket.MSG_OOB)
        elif cmd == WILL:
            if opt == TTYPE:
                self.send(TelnetResponses.TELNET_TERM_QUERY)
            elif opt == LINEMODE:
                self.send(TelnetResponses.TELNET_DONT_LINEMODE)
            elif opt == ECHO or opt == NAWS:
                # do nothing, don't send DONT
                pass
            else:
                self.send(IAC + DONT + opt)
        elif cmd == WONT:
            if opt == LINEMODE:
                self.send(TelnetResponses.TELNET_DONT_LINEMODE)
        elif cmd == DO:
            if opt == TM:
                self.send(TelnetResponses.TELNET_DO_TM_RESPONSE)
            elif opt == SGA:
                self.send(TelnetResponses.TELNET_WILL_SGA)
            elif opt == ECHO:
                # do nothing, don't send WONT
                pass
            else:
                self.send(IAC + WONT + opt)
        elif cmd == DONT:
            if opt == SGA:
                raise RuntimeError('Client requested "DONT SGA": not supported')
        elif cmd == SE:
            cmd = bytes([opt[0]])
            if cmd == NAWS:
                if len(opt) == 5:
                    width = opt[1] << 16 + opt[2]
                    height = opt[3] << 16 + opt[4]
                elif len(opt) == 3:
                    width = opt[1]
                    height = opt[2]
                else:
                    width = 80
                    height = 24
                raise WindowSize(width, height)
            elif cmd == TTYPE:
                if opt[1] == 0:
                    termtype = opt[2:]
                else:
                    termtype = opt[1:]
                raise TerminalType(termtype.decode())

