from io import BytesIO
from collections import OrderedDict
import datetime
import os
import sys
import cgi
from urllib import parse as urlparse

from .stream import InputStream, LineTooLong, ConnectionClosed

import greenlet

class CriticalError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__()

default_404 = b"""
<!DOCTYPE html>
<html>
    <head>
        <title>404 Page Not Found</title>
    </head>
    <body>
        <h1>404 - Page Not Found</h1>
    </body>
</html>
"""

class critical(object):
    entity_too_large = (
        b'HTTP/1.1 413 Request Entity Too Large\r\n'
        b'Content-Length: 0\r\n'
        b'Connection: close\r\n'
        b'\r\n')
    bad_request = (
        b'HTTP/1.1 400 Bad Request\r\n'
        b'Content-Length: 0\r\n'
        b'Connection: close\r\n'
        b'\r\n')
    method_not_allowed = (
        b'HTTP/1.1 405 Method Not Allowed\r\n'
        b'Content-Length: 0\r\n'
        b'Connection: close\r\n'
        b'\r\n')
    internal_server_error = (
        b'HTTP/1.1 500 Internal Server Error\r\n'
        b'Content-Length: 0\r\n'
        b'Connection: close\r\n'
        b'\r\n')

def split_header(value):
    return value.split(',') # naive implementation, fix to account quotes

def format_rfc1123(dt=None):
    """Return a string representation of a date according to RFC 1123 (HTTP/1.1)

    The supplied date must be timestamp or datetime.datetime in UTC.
    """
    if dt is None:
        dt = datetime.datetime.utcnow()
    elif isinstance(dt, (int, float)):
        dt = datetime.datetime.utcfromtimestamp(dt)
    weekday = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[dt.weekday()]
    month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec")[dt.month - 1]
    return "{}, {:02d} {} {:04d} {:02d}:{:02d}:{:02d} GMT".format(
        weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)

class Arguments(object):
    __slots__ = ('_request',)
    def __init__(self, request):
        self._request = request

    def __contains__(self, name):
        for key in self._request._server.order:
            getattr(self._request, key)[0]

class Request(object):
    def __init__(self, method, uri, version, headers, socket, server):
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers
        self._socket = socket
        self._server = server
        self._query = None
        self._params = None
        self._cookies = None
        self._post = None

    def environ(self):
        environ = os.environ.copy()
        environ['REQUEST_METHOD'] = self.method
        environ['SCRIPT_NAME'] = ''
        parts = self.uri.split('?', 1)
        environ['PATH_INFO'] = parts[0]
        if len(parts) > 1:
            environ['QUERY_STRING'] = parts[1]
        if 'Content-Type' in self.request.headers:
            environ['CONTENT_TYPE'] = self.request.headers['Content-Type']
        if 'Content-Length' in self.request.headers:
            environ['CONTENT_LENGTH'] = self.request.headers['Content-Length']
        try:
            environ['SERVER_NAME'],environ['SERVER_PORT'] = socket.getsockname()
        except ValueError: #unix socket ?
            if 'Host' in self.headers:
                parts = self.headers['Host'].split(':')
                environ['SERVER_NAME'] = parts[0]
                if len(parts) > 1:
                    environ['SERVER_PORT'] = parts[1]
                else:
                    environ['SERVER_PORT'] = '80'
        environ['SERVER_PROTOCOL'] = 'HTTP/{}.{}'.format(*self.request.version)
        for k, v in self.request.headers:
            environ['HTTP_'+k.upper().replace('-', '_')] = v
        environ['wsgi.version'] = (1, 0)
        environ['wsgi.uri_scheme'] = 'http'
        environ['wsgi.input'] = self.body
        environ['wsgi.errors'] = sys.stderr
        environ['wsgi.multithread'] = True
        environ['wsgi.multiprocess'] = True
        environ['wsgi.run_once'] = False
        return environ

    @property
    def query(self):
        if self._query is None:
            prt = self.uri.split('?', 1)
            if len(prt) > 1:
                self._query = urlparse.parse_qsl(prt[1], keep_blank_values=True)
            else:
                self._query = {}
        return self._query

    @property
    def post(self):
        if self._post is None:
            if self.method in ('GET', 'HEAD'):
                self._post = {}
            try:
                clen = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise CriticalError('bad_request')
            if clen > 0:
                ctype = self.headers.get('Content-Type',
                    'application/x-www-form-urlencoded').strip()
                if ctype.startswith('application/x-www-form-urlencoded'):
                    buf = BytesIO()
                    while True:
                        chunk = self.body.read(16384)
                        if not chunk:
                            break
                        buf.write(chunk)
                    self._post = urlparse.parse_qsl(
                        buf.getvalue().decode('ascii'),
                        keep_blank_values=True)
                elif ctype.startswith('multipart/form-data'):
                    fs = cgi.FieldStorage(self.body, environ=environ,
                        keep_blank_values=True)
                    self._post = dict((k, fs[k] if fs[k].filename
                        else fs.getlist(k)) for k in fs)
                else:
                    self._post = {}
            else:
                self._post = {}
        return self._post

class Response(object):
    def __init__(self, request):
        self.state = None
        self.request = request
        request.response = self
        self._status = None
        self.headers = OrderedDict()
        self._socket = request._socket
        self._server = request._server
        self.headers['Server'] = self._server.server_name
        self.headers['Date'] = format_rfc1123()
        if request.version == (1, 0):
            self.headers['Connection'] = 'close'

    def status(self, code, string):
        self._status = (code, string)

    def add_header(self, name, value):
        name = self._server.norm_header(name)
        if name in self.headers:
            if name in self._server.multi_headers:
                if isinstance(value, str):
                    value = split_header(value)
                self.headers[name].extend(value)
            else:
                raise ValueError("Header {!r} is already defined".format(name))
        else:
            self.set_header(name, value)

    def set_header(self, name, value):
        if name in self._server.multi_headers:
            if isinstance(value, str):
                value = split_header(value)
        else:
            value = str(value)
        self.headers[name] = value

    def make_response(self):
        buf = BytesIO()
        buf.write('HTTP/1.1 {:3d} {}\r\n'.format(*self._status).encode('ascii'))
        for k, v in self.headers.items():
            if isinstance(v, str):
                buf.write('{}: {}\r\n'.format(k, v).encode('ascii'))
            else:
                buf.write('{}: {}\r\n'.format(k, ', '.join(v)).encode('ascii'))
        buf.write(b'\r\n')
        return buf

    def send_body(self, value):
        if self.state is None:
            if 'Content-Length' in self.headers:
                if int(self.headers['Content-Length']) != len(value):
                    raise RuntimeError("Wrong number of bytes sent")
            else:
                self.add_header('Content-Length', str(len(value)))
            buf = self.make_response()
            buf.write(value)
            buf.seek(0, 0)
            while True:
                data = buf.read(self._server.buffer_size)
                if not data:
                    break
                bytes = self._socket.send(data)
                if bytes < len(data):
                    buf.seek(bytes - len(data), 2)
            self.state = 'done'
        else:
            raise RuntimeError("Response body is being sent twice")

class BodyFixed(object):
    __slots__ = ('to_go', 'stream')
    def __init__(self, length, stream):
        assert length >= 0, length
        self.to_go = length
        self.stream = stream

    def read(self, bytes):
        if not self.to_go:
            return b''
        if bytes > self.to_go:
            bytes = self.to_go
        res = self.stream.read(bytes)
        if not res and self.to_go:
            raise ConnectionClosed("Premature disconnect while reading request body")
        self.to_go -= len(res)
        return res

    def getvalue(self):
        res = self.stream.readblock(self.to_go)
        self.to_go -= len(res)
        return res

    @property
    def done(self):
        return not self.to_go

class BodyChunked(object):
    __slots__ = ('socket', 'lastchunk', 'buf')
    def __init__(self, socket):
        self.socket = socket
        self.glet = greenlet.greenlet(self._read)
        self.glet.switch()

    def read(self, bytes):
        return self.glet.switch(bytes)

    def _read(self):
        buf = b''
        lastchunk = 0
        while True:
            raise NotImplementedError()

    def _readchunk(self, bytes):
        if self.lastchunk < bytes:
            bytes = self.lastchunk
        res = self.socket.recv(bytes)
        if not res:
            raise ConnectionClosed("Premature disconnect while reading request body")
        return res


class BodyClose(object):
    __slots__ = ('socket', 'done')
    def __init__(self, socket):
        self.socket = socket
        self.done = False

    def read(self, bytes):
        data = self.socket.recv(bytes)
        if not data:
            self.done = True
        return data

class _BaseHTTP(object):
    _versions = {
        'HTTP/1.0': (1, 0),
        'HTTP/1.1': (1, 1),
        }
    multi_headers = frozenset((
        'Accept-Charset',
        'Accept-Encoding',
        'Accept-Language',
        'Accept-Ranges',
        'Cache-Control',
        'Connection',
        'Content-Encoding',
        'Content-Language',
        'Expect',
        'If-Match',
        'If-None-Match',
        'Pragma',
        'Proxy-Authenticate',
        'Trailer',
        'Transfer-Encoding',
        'Upgrade',
        'Vary',
        'Via',
        'Warning',
        'WWW-Authenticate',
        ))
    no_body_methods = frozenset((
        'GET',
        'HEAD',
        ))

    def parse_headers(self, data):
        lines = iter(data.splitlines())
        first = next(lines)
        try:
            method, uri, version = first.decode('ascii').strip().split()
            version = self._versions[version]
        except (ValueError, KeyError):
            raise CriticalError('bad_request')
        if method not in self.allow_methods:
            raise CriticalError('method_not_allowed')
        headers = OrderedDict()
        for line in lines:
            if not line:
                break
            try:
                name, value = line.decode('ascii').split(':', 1)
            except ValueError:
                raise CriticalError('bad_request')
            name = self.norm_header(name)
            if name in self.multi_headers:
                value = [v.strip() for v in value.split(',')]
                if name in headers:
                    headers[name].extend(value)
                else:
                    headers[name] = value
            else:
                value = value.strip()
                if name in headers:
                    raise CriticalError('bad_request')
                else:
                    headers[name] = value
        return method, uri, version, headers

    @staticmethod
    def norm_header(value):
        value = value.strip().title()
        if value.startswith('Www-'):
            return 'WWW-' + value[4:] # sorry, silly convention
        else:
            return value

def respond_static(code, string, content_type, data):
    def responder(req):
        resp = Response(req)
        resp.status(code, string)
        resp.add_header('Content-Type', content_type)
        resp.add_header('Content-Length', len(data))
        resp.send_body(data)
        return
    return responder

class Server(_BaseHTTP):
    buffer_size = 4096
    max_headers = 16384
    max_in_memory_body = 256 << 10 # 256Kb
    allow_methods = frozenset(('GET', 'HEAD', 'POST'))
    max_request_body = 100 << 20 # 100Mb
    server_name = "Tyderium/0.1"
    request_factory = Request
    arguments_order = ('query', 'post')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def make_request(self, method, uri, version, headers, socket, stream):
        req = self.request_factory(method, uri, version, headers,
            socket=socket, server=self)
        if 'Transfer-Encoding' in headers:
            raise CriticalError('bad_request')
        if 'Content-Length' in headers:
            try:
                size = int(headers['Content-Length'])
            except ValueError:
                raise CriticalError('bad_request')
            req.body = BodyFixed(size, stream)
        elif version == (1, 0) or \
            'close' in headers.get('Connection', ()):
            req.body = BodyClose(stream)
        elif method in self.no_body_methods:
            req.body = BodyFixed(0, stream)
        else:
            raise CriticalError('bad_request')
        return req

    def clean_request(self, req):
        while not req.body.done:
            req.body.read(self.buffer_size)
        if not hasattr(req, 'response') or not req.response.status != 'done':
            # This error is critical, because something bad may happen
            # e.g. we have written some data but not finished, or not
            # marked status as "done", etc.
            raise CriticalError('internal_server_error')
        if req.version == (1, 0):
            req._socket.close()
        # Remove reference to sockets in case someone remember that objects
        req.response._socket = None
        req._socket = None
        # Remove cyclic links
        req.response.request = None
        req.response = None

    def __call__(self, socket, addr):
        stream = InputStream(socket)
        try:
            while True:
                headers = stream.readline(b'\r\n\r\n', maxlen=self.max_headers)
                req = self.make_request(*self.parse_headers(headers),
                    socket=socket, stream=stream)
                self.response_factory(req)
                self.clean_request(req)
        except LineTooLong:
            socket.sendall(critical.entity_too_large)
        except CriticalError as e:
            socket.sendall(getattr(critical, e.message))
        except ConnectionClosed:
            pass
        except Exception as e:
            sys.excepthook(*sys.exc_info())
            socket.sendall(critical.internal_server_error)
        finally:
            socket.close()

if __name__ == '__main__':
    from .hub import Hub
    from .server import Listener
    resp = respond_static(200, 'OK', 'text/html', b"HELLO")
    with Hub() as hub:
        l1 = Listener(('127.0.0.1', 8080), Server(response_factory=resp))
        print("Listening on", l1.addr)
        hub.spawn(l1.serve)
        hub.switch()
