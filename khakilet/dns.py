from . import lib as ev, hub

from greenlet import getcurrent
from socket import AF_INET, AF_INET6

import ctypes
import os
import struct
import sys


if sys.platform == 'win32':
    lib = ctypes.CDLL('libudns.dll')
    libc = ctypes.CDLL(ctypes.util.find_msvcrt())
else:
    lib = ctypes.CDLL('libudns.so')
    libc = ctypes.CDLL('libc.so.6')

free = libc.free
free.argtypes = [ctypes.c_void_p]

lib.dns_init(0, 0)

lib.dns_ntop.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
lib.dns_pton.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p]

class DNSLookupError(LookupError): pass


class DNSContext(ctypes.Structure):
    """Class just for type checking"""
    _fields_ = [('_blank_', ctypes.c_void_p)]


class In_Addr(ctypes.Structure):
    _fields_ = [
        ('s_addr', ctypes.c_uint)
        ]

    def __repr__(self):
        buf = ctypes.create_string_buffer(256)
        src = ctypes.addressof(self)
        lib.dns_ntop(AF_INET, src, buf, 256)
        return ctypes.string_at(buf).decode()

class QueryA(ctypes.Structure):
    _fields_ = [
        ('dnsa_qname', ctypes.c_char_p),
        ('dnsa_cname', ctypes.c_char_p),
        ('dnsa_ttl', ctypes.c_uint),
        ('dnsa_nrr', ctypes.c_int),
        ('dnsa_void', ctypes.c_void_p),
        ('dnsa_addr', In_Addr * 16)
        ]


QueryA.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryA), ctypes.py_object)

class In6_Addr(ctypes.Structure):
    _fields_ = [
        ('s_addr', ctypes.c_uint * 4)
        ]

    def __repr__(self):
        buf = ctypes.create_string_buffer(256)
        src = ctypes.addressof(self)
        lib.dns_ntop(AF_INET6, src, buf, 256)
        return ctypes.string_at(buf).decode()

class QueryAAAA(ctypes.Structure):
    _fields_ = [
        ('dnsa_qname', ctypes.c_char_p),
        ('dnsa_cname', ctypes.c_char_p),
        ('dnsa_ttl', ctypes.c_uint),
        ('dnsa_nrr', ctypes.c_int),
        ('dnsa_void', ctypes.c_void_p),
        ('dnsa_addr', In6_Addr * 16)
        ]

QueryAAAA.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryAAAA), ctypes.py_object)

class QueryAPtr(ctypes.Structure):
    _fields_ = [
        ('dnsptr_qname', ctypes.c_char_p),
        ('dnsptr_cname', ctypes.c_char_p),
        ('dnsptr_ttl', ctypes.c_uint),
        ('dnsptr_nrr', ctypes.c_int),
        ('dnsptr_void', ctypes.c_void_p),
        ('dnsptr_ptr', ctypes.c_char_p*256),
        ]

QueryAPtr.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryAPtr), ctypes.py_object)

class QueryAAAAPtr(ctypes.Structure):
    _fields_ = [
        ('dnsptr_qname', ctypes.c_char_p),
        ('dnsptr_cname', ctypes.c_char_p),
        ('dnsptr_ttl', ctypes.c_uint),
        ('dnsptr_nrr', ctypes.c_int),
        ('dnsptr_void', ctypes.c_void_p),
        ('dnsptr_ptr', ctypes.c_char_p*256),
        ]

QueryAAAAPtr.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryAAAAPtr), ctypes.py_object)


class Query_Id():
    _value = 0

    @staticmethod
    def next():
        Query_Id._value += 1
        return Query_Id._value


class Query:
    def __init__(self):
        self.__query_id = Query_Id.next()
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
            callback = QueryA.Callback(self._a_callback)
            self.__query = lib.dns_submit_a4(_resolverservice.context, hostenc, 0,
                callback, ctypes.py_object(self.__branch))
        elif af == AF_INET6:
            callback = QueryAAAA.Callback(self._a_callback)
            self.__query = lib.dns_submit_a6(_resolverservice.context, hostenc, 0,
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
        if af == AF_INET:
            addr = In_Addr()
            if 0 >= lib.dns_pton(af, ip.encode('utf-8'), ctypes.addressof(addr)):
                raise ValueError('Not a valid AF_INET address: %s' % ip)
            callback = QueryAPtr.Callback(self._ptr_callback)
            self.__query = lib.dns_submit_a4ptr(
                _resolverservice.context, ctypes.addressof(addr), callback, ctypes.py_object(self.__branch))
        elif af == AF_INET6:
            addr = In6_Addr()
            if 0 >= lib.dns_pton(af, ip.encode('utf-8'), ctypes.addressof(addr)):
                raise ValueError('Not a valid AF_INET6 address: %s' % ip)
            callback = QueryAPtr.Callback(self._ptr_callback)
            self.__query = lib.dns_submit_a6ptr(
                _resolverservice.context, ctypes.addressof(addr), callback, ctypes.py_object(self.__branch))
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
                lib.dns_cancel(_resolverservice.context, self.__query)
            self.__branch.throw(DNSLookupError)

    def _a_callback(self, _context, query, branch):
        try:
            if self.__state != 'timeout':
                if not query:
                    branch.throw(DNSLookupError)
                else:
                    branch.switch([repr(x) for x in query[0].dnsa_addr[:query[0].dnsa_nrr]])
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
        self.context = lib.dns_new(None)
        self.iowatch = ev.Io(fd=lib.dns_open(self.context), events=ev.EV_READ)
        self.iowatch.branch = self
        self.pipe = os.pipe()
        self.pipewatch = ev.Io(fd=self.pipe[0], events=ev.EV_READ)
        self.pipewatch.branch = self
        self.queries = dict()
        self.running = True

    def __del__(self):
        lib.dns_free(self.context)

    def add_query(self, query):
        self.queries[query.query_id] = query

    def remove_query(self, query):
        self.queries.pop(query.query_id)

    def run(self, reason=None):
        self.hub.add_watch(self.iowatch, 'io', single=False)
        self.hub.add_watch(self.pipewatch, 'pipe', single=False)

        try:
            while self.running:
                lib.dns_timeouts(self.context, -1, 0)

                if reason == 'io':
                    lib.dns_ioevent(self.context, 0)
                elif reason == 'pipe':
                    os.read(self.pipe[0], 64)
                elif not reason or reason == 'request':
                    pass
                else:
                    # timeout, treat reason as id
                    try:
                        query = self.queries.pop(reason)
                        if query:
                            query.timeout()
                    except KeyError:
                        pass
                reason = self.hub.switch()
        finally:
            self.hub.remove_watch(self.iowatch)
            self.hub.remove_watch(self.pipewatch)

        del self.iowatch
        del self.pipewatch
        del self.queries

        os.close(self.pipe[0])
        os.close(self.pipe[1])

    def stop(self):
        self.running = False
        self.__notify()

        #for query in list(self.queries.values()):
            #query.timeout()

    def __notify(self):
        os.write(self.pipe[1], b'*')


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


if __name__ == '__main__':
    count = 100

    names = [
        ('ipv6.google.com', AF_INET6),
        ('www.google.com', AF_INET),
        ('www.yahoo.com', AF_INET),
        ('ipv6.comcast.net', AF_INET6),
        ('www.microsoft.com', AF_INET),
        ('apple.com', AF_INET),
        ('slashdot.org', AF_INET),
    ]

    def resolve(name, af):
        try:
            addr = gethostbyname(name, timeout=10.0, af=af)
            n = gethostbyaddr(addr, timeout=10.0, af=af)
        except DNSLookupError:
            addr = 'unknown'
            n = 'n/a'
        print(name, addr, n)
        global count
        count -= 1
        if count <= 0:
            stop_resolver_service()
            hub.stop()

    from .hub import Hub
    with Hub() as hub:
        start_resolver_service(hub)
        for i in range(0, count):
            name, af = names[i % len(names)]
            hub.spawn(resolve, name, af)
        hub.switch()

