import os, os.path
from greenlet import getcurrent

from . import socket

class Listener(object):
    def __init__(self, addr, factory, listen_backlog=128, spawn=True, fd=None, pf=socket.AF_INET):
        if pf == socket.AF_UNIX:
            self.sock = socket.socket(pf, socket.SOCK_STREAM, 0, fd)
            if fd is None and os.path.exists(addr):
                try:
                    self.sock.connect(addr)
                except socket.error:
                    os.unlink(addr)
                else:
                    self.sock.close()
                    raise socket.error("Address is still in use")
        else:
            self.sock = socket.socket(pf, socket.SOCK_STREAM, 0, fd)
            if fd is None:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            if fd is None:
                self.sock.bind(addr)
                self.sock.listen(listen_backlog)
            self.factory = factory
            self.spawn = spawn
            self.addr = self.sock.getsockname()
        except:
            self.sock.close()
            raise

    def serve(self):
        hub = getcurrent().hub
        while True:
            sock, addr = self.sock.accept()
            if self.spawn:
                hub.spawn(self.factory, sock, addr)
            else:
                self.factory(sock, addr)

    def serve_forever(self):
        from .hub import Hub
        with Hub() as hub:
            hub.spawn(self.serve)
            hub.switch()

    def close(self):
        self.sock.close()

if __name__ == '__main__':
    def echo(socket, addr):
        s = socket.recv(4096)
        while s:
            socket.send(s)
            s = socket.recv(4096)

    import sys
    from operator import attrgetter
    from .hub import Hub
    with Hub() as hub:
        all = []
        all.append(Listener(('127.0.0.1', 0), echo))
        all.append(Listener(('127.0.0.1', 8080), echo))
        if sys.platform != 'win32':
            import os
            if os.path.exists('./testsock'):
                os.unlink('./testsock')
            all.append(Listener('./testsock', echo, pf=socket.AF_UNIX))
        print("Listening on", ', '.join(map(repr, map(attrgetter('addr'), all))))
        for val in all:
            hub.spawn(val.serve)
        hub.switch()
