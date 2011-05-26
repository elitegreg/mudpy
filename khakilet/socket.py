import socket as stdsocket
import errno
from . import lib
import greenlet

from socket import * # for convenience

class socket(stdsocket.socket):
    __slots__ = ()
    def __init__(self, *args):
        super().__init__(*args)
        self.setblocking(False)

    def connect(self, value):
        ret = self.connect_ex(value)
        if ret == 0:
            return
        if ret != errno.EINPROGRESS:
            raise stdsocket.error(ret)
        lib.Io(fd=self.fileno(), events=lib.EV_WRITE).start()

    def send(self, value):
        while True:
            lib.Io(fd=self.fileno(), events=lib.EV_WRITE)
            try:
                return super().send(value)
            except stdsocket.error as err:
                if err.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    continue
                raise

    def sendall(self, value):
        while True:
            bytes = self.send(value)
            if bytes >= len(value):
                return
            value = value[bytes:]

    def recv(self, size):
        while True:
            fd = self.fileno()
            if fd < 0:
                return b''
            lib.Io(fd=fd, events=lib.EV_READ).start()
            try:
                return super().recv(size)
            except stdsocket.error as err:
                if err.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    continue
                raise

    def accept(self):
        while True:
            lib.Io(fd=self.fileno(), events=lib.EV_READ).start()
            try:
                sock, addr = super().accept()
                sock.setblocking(False)
                sock.__class__ = socket
                return sock, addr
            except stdsocket.error as err:
                if err.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    continue
                raise

def fromfd(*args):
    sock = stdsocket.fromfd(*args)
    sock.__class__ = socket
    return sock

if __name__ == '__main__':
    from .hub import Hub
    def get():
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect(('127.0.0.1', 8000))
        sock.send(b'GET / HTTP/1.0\r\n\r\n') # wrong but ok for sample
        sock.shutdown(SHUT_WR)
        while True:
            data = sock.recv(4096)
            if not data:
                break
            print(data)
    while True:
        with Hub() as hub:
            hub.spawn(get)
            hub.switch()

