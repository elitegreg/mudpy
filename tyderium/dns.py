from . import lib as ev, hub

from greenlet import getcurrent
from socket import AF_INET, AF_INET6

import ctypes
import os
import struct
import sys


__all__ = [
    'DNSLookupError',
    'Query',
    'start_resolver_service',
    'stop_resolver_service',
    'gethostbyaddr',
    'gethostbyname',
]

if sys.platform == 'win32':
    _lib = ctypes.CDLL('libudns.dll')
else:
    _lib = ctypes.CDLL('libudns.so')

_lib.dns_init(0, 0)
_lib.dns_ntop.argtypes = \
        [ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_lib.dns_pton.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p]

class DNSLookupError(LookupError): pass


class _DNSContext(ctypes.Structure):
    """Class just for type checking"""
    _fields_ = [('_blank_', ctypes.c_void_p)]


class _In_Addr(ctypes.Structure):
    _fields_ = [
        ('s_addr', ctypes.c_uint)
        ]

    def __repr__(self):
        buf = ctypes.create_string_buffer(256)
        src = ctypes.addressof(self)
        _lib.dns_ntop(AF_INET, src, buf, 256)
        return ctypes.string_at(buf).decode()

class _QueryA(ctypes.Structure):
    _fields_ = [
        ('dnsa_qname', ctypes.c_char_p),
        ('dnsa_cname', ctypes.c_char_p),
        ('dnsa_ttl', ctypes.c_uint),
        ('dnsa_nrr', ctypes.c_int),
        ('dnsa_void', ctypes.c_void_p),
        ('dnsa_addr', _In_Addr * 16)
        ]


_QueryA.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_DNSContext),
    ctypes.POINTER(_QueryA), ctypes.py_object)

class _In6_Addr(ctypes.Structure):
    _fields_ = [
        ('s_addr', ctypes.c_uint * 4)
        ]

    def __repr__(self):
        buf = ctypes.create_string_buffer(256)
        src = ctypes.addressof(self)
        _lib.dns_ntop(AF_INET6, src, buf, 256)
        return ctypes.string_at(buf).decode()

class _QueryAAAA(ctypes.Structure):
    _fields_ = [
        ('dnsa_qname', ctypes.c_char_p),
        ('dnsa_cname', ctypes.c_char_p),
        ('dnsa_ttl', ctypes.c_uint),
        ('dnsa_nrr', ctypes.c_int),
        ('dnsa_void', ctypes.c_void_p),
        ('dnsa_addr', _In6_Addr * 16)
        ]

_QueryAAAA.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_DNSContext),
    ctypes.POINTER(_QueryAAAA), ctypes.py_object)

class _QueryPtr(ctypes.Structure):
    _fields_ = [
        ('dnsptr_qname', ctypes.c_char_p),
        ('dnsptr_cname', ctypes.c_char_p),
        ('dnsptr_ttl', ctypes.c_uint),
        ('dnsptr_nrr', ctypes.c_int),
        ('dnsptr_void', ctypes.c_void_p),
        ('dnsptr_ptr', ctypes.c_char_p*256),
        ]

_QueryPtr.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_DNSContext),
    ctypes.POINTER(_QueryPtr), ctypes.py_object)

class _Query_Id():
    _value = 0

    @staticmethod
    def next():
        _Query_Id._value += 1
        return _Query_Id._value


class Query:
    def __init__(self):
        self.__query_id = _Query_Id.next()
        self.__state = 'new'
        self.__branch = None
        self.__query = None

    def __query_common(self, timeout):
        self.__towatch = ev.Timer(timeout)
        _resolverservice.add_query(self)
        _resolverservice.hub.add_watch(
            self.__towatch, self.__query_id, single=False)
        self.__towatch.branch = _resolverservice

    def a_record(self, hostname, timeout=1.0, af=AF_INET):
        if self.__state != 'new':
            raise ValueError('bad state')
        self.__state = 'request'
        self.__query_common(timeout)
        self.__branch = getcurrent()
        hostenc = hostname.encode('utf-8')
        if af == AF_INET:
            callback = _QueryA.Callback(self._a_callback)
            self.__query = _lib.dns_submit_a4(
                _resolverservice.context, hostenc, 0,
                callback, ctypes.py_object(self.__branch))
        elif af == AF_INET6:
            callback = _QueryAAAA.Callback(self._a_callback)
            self.__query = _lib.dns_submit_a6(
                _resolverservice.context, hostenc, 0,
                callback, ctypes.py_object(self.__branch))
        else:
            raise TypeError('bad address family')
        self.__af = af
        return _resolverservice.switch('request')

    def ptr_record(self, ip, timeout=1.0, af=AF_INET):
        if self.__state != 'new':
            raise ValueError('bad state')
        self.__state = 'request'
        self.__query_common(timeout)
        self.__branch = getcurrent()
        ip = ip.encode('ascii')
        if af == AF_INET:
            addr = _In_Addr()
            if 0 >= _lib.dns_pton(af, ip, ctypes.addressof(addr)):
                raise ValueError('Not a valid AF_INET address: %s' % ip)
            callback = _QueryPtr.Callback(self._ptr_callback)
            self.__query = _lib.dns_submit_a4ptr(
                _resolverservice.context, ctypes.addressof(addr),
                callback, ctypes.py_object(self.__branch))
        elif af == AF_INET6:
            addr = _In6_Addr()
            if 0 >= _lib.dns_pton(af, ip, ctypes.addressof(addr)):
                raise ValueError('Not a valid AF_INET6 address: %s' % ip)
            callback = _QueryPtr.Callback(self._ptr_callback)
            self.__query = _lib.dns_submit_a6ptr(
                _resolverservice.context, ctypes.addressof(addr),
                callback, ctypes.py_object(self.__branch))
        else:
            raise TypeError('bad address family')
        self.__af = af
        return _resolverservice.switch('request')

    @property
    def query_id(self):
        return self.__query_id

    def timeout(self):
        if self.__state != 'timeout':
            self.__state = 'timeout'
            if self.__query:
                _lib.dns_cancel(_resolverservice.context, self.__query)
            self.__branch.throw(DNSLookupError)

    def _a_callback(self, _context, query, branch):
        try:
            if self.__state != 'timeout':
                if not query:
                    branch.throw(DNSLookupError)
                else:
                    branch.switch([repr(x)
                            for x in query[0].dnsa_addr[:query[0].dnsa_nrr]])
        finally:
            _resolverservice.remove_query(self)
            self.__query = None

    def _ptr_callback(self, _context, query, branch):
        try:
            if self.__state != 'timeout':
                if not query:
                    branch.throw(DNSLookupError)
                else:
                    branch.switch([val.decode('utf-8')
                        for val in query[0].dnsptr_ptr[:query[0].dnsptr_nrr]])
        finally:
            _resolverservice.remove_query(self)
            self.__query = None


def start_resolver_service(hub):
    global _resolverservice
    _resolverservice = _ResolverService(hub)
    hub.spawn(_resolverservice.switch)


def stop_resolver_service():
    global _resolverservice
    _resolverservice.stop()
    _resolverservice = None


class _ResolverService(hub.Branch):
    def __init__(self, hub, **kwargs):
        super().__init__(hub=hub, **kwargs)
        self.__context = _lib.dns_new(None)
        self.__iowatch = ev.Io(
            fd=_lib.dns_open(self.__context), events=ev.EV_READ)
        self.__iowatch.branch = self
        self.__pipe = os.pipe()
        self.__pipewatch = ev.Io(fd=self.__pipe[0], events=ev.EV_READ)
        self.__pipewatch.branch = self
        self.__queries = dict()
        self.__running = True

    def __del__(self):
        _lib.dns_free(self.__context)

    @property
    def context(self):
        return self.__context

    def add_query(self, query):
        self.__queries[query.query_id] = query

    def remove_query(self, query):
        self.__queries.pop(query.query_id)

    def run(self, reason=None):
        self.hub.add_watch(self.__iowatch, 'io', single=False)
        self.hub.add_watch(self.__pipewatch, 'pipe', single=False)

        try:
            while self.__running:
                _lib.dns_timeouts(self.__context, -1, 0)

                if reason == 'io':
                    _lib.dns_ioevent(self.__context, 0)
                elif reason == 'pipe':
                    os.read(self.__pipe[0], 64)
                elif not reason or reason == 'request':
                    pass
                else:
                    # timeout, treat reason as id
                    try:
                        query = self.__queries.pop(reason)
                        if query:
                            query.timeout()
                    except KeyError:
                        pass
                reason = self.hub.switch()
        finally:
            self.hub.remove_watch(self.__iowatch)
            self.hub.remove_watch(self.__pipewatch)

        del self.__iowatch
        del self.__pipewatch
        del self.__queries

        os.close(self.__pipe[0])
        os.close(self.__pipe[1])

    def stop(self):
        self.__running = False
        self.__notify()
        # TODO cancel outstanding queries?

    def __notify(self):
        os.write(self.__pipe[1], b'*')


def gethostbyname(name, timeout=1.0, af=None):
    if af is None:
        try:
            # TODO we shouldn't do this if there is no ipv6 support
            return Query().a_record(name, timeout, AF_INET6)[0]
        except DNSLookupError:
            return Query().a_record(name, timeout, AF_INET)[0]
    else:
        return Query().a_record(name, timeout, af)[0]


def gethostbyaddr(addr, timeout=1.0, af=None):
    if af is None:
        try:
            return Query().ptr_record(addr, timeout, AF_INET6)[0]
        except ValueError:
            return Query().ptr_record(addr, timeout, AF_INET)[0]
    else:
        return Query().ptr_record(addr, timeout, af)[0]

