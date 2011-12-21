from . import lib
from .timeout import Timeout

import greenlet

import errno
import socket as stdsocket

from socket import * # for convenience
from socket import timeout as timeout_error


class socket(stdsocket.socket):
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setblocking(False)
    def __wait(self, events, timeout=None):
        try:
            with Timeout(timeout if timeout else super().gettimeout()):
                lib.Io(fd=self.fileno(), events=events).start()
        except TimeoutError:
            raise timeout_error

    def connect(self, addr, timeout=None):
        ret = self.connect_ex(addr)
        if ret == 0:
            return
        if ret != errno.EINPROGRESS:
            raise stdsocket.error(ret)
        self.__wait(lib.EV_WRITE, timeout)

    def send(self, value, timeout=None, *args, **kwargs):
        while True:
            try:
                return super().send(value, *args, **kwargs)
            except stdsocket.error as err:
                if err.errno not in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    raise
            self.__wait(lib.EV_WRITE, timeout)

    def sendall(self, value, timeout=None, *args, **kwargs):
        while True:
            bytes = self.send(value, timeout, *args, **kwargs)
            if bytes >= len(value):
                return
            value = value[bytes:]

    def recv(self, size, timeout=None, *args, **kwargs):
        while True:
            fd = self.fileno()
            if fd < 0:
                return b''
            self.__wait(lib.EV_READ, timeout)
            try:
                return super().recv(size, *args, **kwargs)
            except stdsocket.error as err:
                if err.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    continue
                raise

    def accept(self, timeout=None):
        while True:
            self.__wait(lib.EV_READ, timeout)
            try:
                sock, addr = super().accept()
                sock.setblocking(False)
                sock.__class__ = socket
                return sock, addr
            except stdsocket.error as err:
                if err.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    continue
                raise

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

