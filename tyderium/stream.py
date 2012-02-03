from .socket import socket

__all__ = ['LineTooLong', 'ConnectionClosed', 'InputStream']

class LineTooLong(IOError): pass
class ConnectionClosed(IOError): pass

class InputStream(socket):
    __slots__ = ('_buf', 'recvfun')
    buffer_size = 8192
    def __init__(self, socket):
        self._buf = b''
        if hasattr(socket, 'recv'):
            self.recvfun = socket.recv
        elif hasattr(socket, 'read'):
            self.recvfun = socket.read
        elif hasattr(socket, '__call__'):
            self.recvfun = socket
        else:
            raise NotImplemenetedError()

    def readline(self, endline=b'\n', maxlen=16384):
        """Reads a line from a socket

        Line returned includes endline string. If connection closed on a
        half-line ``ConnectionClosed`` is raised. You can get data till end of
        file using ``read()`` method

        Use this method for short lines (length of few kilobytes)
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

    def readblock(self, size):
        """Reads a sized block from a socket

        If connection closed before ``size`` bytes are read ``ConnectionClosed``
        is raised. You can get data till end of file using read() method.

        Use this method for short lines (length of few kilobytes)
        """
        if size <= len(self._buf):
            res = self._buf[:size]
            self._buf = b''
            return res
        if size > self.buffer_size: # long block
            buf = BytesIO()
            buf.write(self._buf)
            self._buf = b''
            while buf.tell() < size:
                chunk = self.recvfun(self.buffer_size)
                if not chunk:
                    raise ConnectionClosed()
                buf.write(chunk)
            buf.seek(0, 0)
            res = buf.read(size)
            self._buf = buf.read()
            return res
        else: # short block
            while len(self._buf) < size:
                chunk = self.recvfun(self.buffer_size)
                if not chunk:
                    raise ConnectionClosed()
                self._buf += chunk
            res = self._buf[:size]
            self._buf = self._buf[size:]
            return res

    def read(self, size):
        if self._buf:
            res = self._buf[:size]
            self._buf = self._buf[size:]
            return res
        return self.recvfun(size)
