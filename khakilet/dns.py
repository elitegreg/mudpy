import sys
import ctypes
from greenlet import getcurrent
from . import lib as ev, hub

if sys.platform == 'win32':
    lib = ctypes.CDLL('libudns.dll')
else:
    lib = ctypes.CDLL('libudns.so')

lib.dns_init(0, 0)

class DNSLookupError(LookupError): pass
class A4NotFound(DNSLookupError): pass
class A4PtrNotFound(DNSLookupError): pass

class DNSContext(ctypes.Structure):
    """Class just for type checking"""
    _fields_ = [('_blank_', ctypes.c_void_p)]

class QueryA4(ctypes.Structure):
    _fields_ = [
        ('dnsa4_qname', ctypes.c_char_p),
        ('dnsa4_cname', ctypes.c_char_p),
        ('dnsa4_ttl', ctypes.c_uint),
        ('dnsa4_nrr', ctypes.c_int),
        ('dnsa4_unknown', ctypes.c_int),
        ('dnsa4_addr', ctypes.c_ubyte*4*100),
        ]

QueryA4.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryA4), ctypes.py_object)

class QueryA4Ptr(ctypes.Structure):
    _fields_ = [
        ('dnsptr_qname', ctypes.c_char_p),
        ('dnsptr_cname', ctypes.c_char_p),
        ('dnsptr_ttl', ctypes.c_uint),
        ('dnsptr_nrr', ctypes.c_int),
        ('dnsptr_unknown', ctypes.c_int),
        ('dnsptr_ptr', ctypes.c_char_p*100),
        ]

QueryA4Ptr.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(DNSContext),
    ctypes.POINTER(QueryA4Ptr), ctypes.py_object)

class Resolver(hub.Branch):
    __slots__ = ('context', 'iowatch', 'towatch', 'greenlet')
    timeout = 3.0 #seconds to keep dns socket open

    def __init__(self, hub, **kwargs):
        super().__init__(hub=hub, **kwargs)
        self.context = lib.dns_new(None)
        self.iowatch = ev.Io(fd=lib.dns_open(self.context), events=ev.EV_READ)
        self.iowatch.branch = self
        self.towatch = ev.Timer(self.timeout)
        self.towatch.branch = self

    def __del__(self):
        lib.dns_free(self.context)

    def run(self, reason):
        assert reason == 'request', "started with reason {!r}".format(reason)
        self.hub.add_watch(self.iowatch, 'io', single=False)
        self.hub.add_watch(self.towatch, 'timeo', single=False)
        newto = lib.dns_timeouts(self.context, -1, 0)
        assert newto > 0, newto
        self.towatch.shift(self.hub, newto)
        active = True
        try:
            while True:
                reason = self.hub.switch()
                if reason == 'io':
                    lib.dns_ioevent(self.context, 0)
                elif reason == 'timeo':
                    if not active:
                        break
                elif reason == 'request':
                    active = True
                    continue
                else:
                    raise ValueError(reason)
                newto = lib.dns_timeouts(self.context, -1, 0)
                if newto < 0:
                    active = False
                    self.towatch.shift(self.hub, self.timeout)
                else:
                    self.towatch.shift(self.hub, newto)

        finally:
            self.hub.remove_watch(self.iowatch)
            self.hub.remove_watch(self.towatch)
        del self.iowatch
        del self.towatch

    @classmethod
    def _instance(cls):
        hub = getcurrent().hub
        try:
            self = hub.__instance
        except AttributeError:
            self = cls(hub=hub)
            hub.__instance = self
        return self

    def _a4_callback(self, _context, query, branch):
        if not query:
            branch.switch([])
        else:
            branch.switch(['{:d}.{:d}.{:d}.{:d}'.format(a[0], a[1], a[2], a[3])
                for a in query[0].dnsa4_addr[:query[0].dnsa4_nrr]])

    def submit_a4(self, hostname):
        cur = getcurrent()
        callback = QueryA4.Callback(self._a4_callback)
        hostenc = hostname.encode('ascii')
        lib.dns_submit_a4(self.context, hostenc, 0,
            callback, ctypes.py_object(cur))
        result = self.switch('request')
        hub = cur.hub
        w = ev.Idle()
        w.branch = cur
        hub.add_watch(w)
        self.switch() # back to udns and return in idle watch
        return result

    @classmethod
    def get_a4(cls, hostname):
        return cls._instance().submit_a4(hostname)

    def _a4ptr_callback(self, _context, query, branch):
        if not query:
            branch.switch([])
        else:
            branch.switch([val.decode('ascii')
                for val in query[0].dnsptr_ptr[:query[0].dnsptr_nrr]])

    def submit_a4ptr(self, ip):
        cur = getcurrent()
        callback = QueryA4Ptr.Callback(self._a4ptr_callback)
        items = map(int, ip.split('.'))
        ip = (ctypes.c_ubyte*4)(*items)
        lib.dns_submit_a4ptr(self.context, ip, callback, ctypes.py_object(cur))
        result = self.switch('request')
        hub = cur.hub
        w = ev.Idle()
        w.branch = cur
        hub.add_watch(w)
        self.switch() # back to udns and return in idle watch
        return result

    @classmethod
    def get_a4ptr(cls, ip):
        return cls._instance().submit_a4ptr(ip)

def gethostbyname(name):
    ips = Resolver.get_a4(name)
    try:
        return ips[0]
    except:
        raise A4NotFound(name)

if __name__ == '__main__':
    testdomains = (
        'google.com',
        'yahoo.com',
        'yandex.ru',
        'bit.ly',
        'twitter.com',
        'non.existent.domain',
        )
    def resolve(name):
        try:
            addr = gethostbyname(name)
            reverse = Resolver.get_a4ptr(addr)
        except A4NotFound:
            addr = 'unknown'
            reverse = ['unknown']
        except:
            print("EXCEPTION")
            raise
        print(name, addr, reverse[0] if reverse else 'unknown')
    from .hub import Hub
    with Hub() as hub:
        for name in testdomains:
            hub.spawn(resolve, name)
        hub.switch()
