import ctypes
import sys
from greenlet import getcurrent

EVLOOP_NONBLOCK = 1
EVLOOP_ONESHOT  = 2
EVUNLOOP_CANCEL = 0
EVUNLOOP_ONE    = 1
EVUNLOOP_ALL    = 2
EV_UNDEF        = -1            # guaranteed to be invalid
EV_NONE         = 0x00          # no events
EV_READ         = 0x01          # ev_io detected read will not block
EV_WRITE        = 0x02          # ev_io detected write will not block
EV__IOFDSET     = 0x80          # internal use only
EV_IO           = EV_READ       # alias for type-detection
EV_TIMEOUT      = 0x00000100    # timer timed out
EV_TIMER        = EV_TIMEOUT    # alias for type-detection
EV_PERIODIC     = 0x00000200    # periodic timer timed out
EV_SIGNAL       = 0x00000400    # signal was received
EV_CHILD        = 0x00000800    # child/pid had status change
EV_STAT         = 0x00001000    # stat data changed
EV_IDLE         = 0x00002000    # event loop is idling
EV_PREPARE      = 0x00004000    # event loop about to poll
EV_CHECK        = 0x00008000    # event loop finished poll
EV_EMBED        = 0x00010000    # embedded event loop needs sweep
EV_FORK         = 0x00020000    # event loop resumed in child
EV_ASYNC        = 0x00040000    # async intra-loop signal
EV_CUSTOM       = 0x01000000    # for use by user code
EV_ERROR        = 0x80000000    # sent when an error occurs

if sys.platform == 'win32':
    dll = ctypes.CDLL('libev.dll')
else:
    dll = ctypes.CDLL('libev.so')

class Loop(ctypes.Structure):
    pass

class _Watch(ctypes.Structure):
    __slots__ = ('branch', 'value')

    def __init__(self, value=None):
        self.value = value
        super().__init__(_active=0, _pending=0, _priority=0, _data=0)

    def start(self):
        branch = self.branch = getcurrent()
        branch.hub.add_watch(self)
        branch.hub.switch()

ev_callback = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(Loop), ctypes.c_long, ctypes.c_int)

_Watch._fields_ = [
        ('_active', ctypes.c_int),
        ('_pending', ctypes.c_int),
        ('_priority', ctypes.c_int),
        ('_data', ctypes.c_void_p),
        ('_callback', ev_callback),
        ]

class Io(_Watch):
    __slots__ = ()
    _fields_ = [
        ('_next', ctypes.c_void_p),
        ('fd', ctypes.c_int),
        ('events', ctypes.c_int),
        ]

    def __init__(self, fd, events):
        super().__init__()
        while hasattr(fd, 'fileno'):
            fd = fd.fileno()
        self.fd = fd
        self.events = events | EV__IOFDSET

    def start(self):
        if self.fd < 0:
            raise RuntimeError("Can't watch negative file descriptor")
        super().start()

ev_io_start = dll.ev_io_start
ev_io_start.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Io)]
ev_io_start.restype = None
ev_io_stop = dll.ev_io_stop
ev_io_stop.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Io)]
ev_io_stop.restype = None
Io.start_function = ev_io_start
Io.stop_function = ev_io_stop

class Idle(_Watch):
    __slots__ = ()
    _fields_ = ()

ev_idle_start = dll.ev_idle_start
ev_idle_start.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Idle)]
ev_idle_start.restype = None
ev_idle_stop = dll.ev_idle_stop
ev_idle_stop.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Idle)]
ev_idle_stop.restype = None
Idle.start_function = ev_idle_start
Idle.stop_function = ev_idle_stop

class Timer(_Watch):
    __slots__ = ()
    _fields_ = [
        ('at', ctypes.c_double),
        ('repeat', ctypes.c_double),
        ]

    def __init__(self, at=0.0, repeat=0.0):
        super().__init__()
        self.at = at
        self.repeat = repeat

    def shift(self, hub, value):
        self.repeat = value
        ev_timer_again(hub.handle, self)

ev_timer_start = dll.ev_timer_start
ev_timer_start.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Timer)]
ev_timer_start.restype = None
ev_timer_again = dll.ev_timer_start
ev_timer_again.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Timer)]
ev_timer_again.restype = None
ev_timer_stop = dll.ev_timer_stop
ev_timer_stop.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Timer)]
ev_timer_stop.restype = None
Timer.start_function = ev_timer_start
Timer.stop_function = ev_timer_stop

class Signal(_Watch):
    __slots__ = ()
    _fields_ = [
        ('_next', ctypes.c_void_p),
        ('signum', ctypes.c_int),
        ]

    def __init__(self, signum):
        super().__init__()
        self.signum = signum

ev_signal_start = dll.ev_signal_start
ev_signal_start.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Signal)]
ev_signal_start.restype = None
ev_signal_again = dll.ev_signal_start
ev_signal_again.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Signal)]
ev_signal_again.restype = None
ev_signal_stop = dll.ev_signal_stop
ev_signal_stop.argtypes = [ctypes.POINTER(Loop), ctypes.POINTER(Signal)]
ev_signal_stop.restype = None
Signal.start_function = ev_signal_start
Signal.stop_function = ev_signal_stop

ev_loop_new = dll.ev_loop_new
ev_loop_new.argtypes = [ctypes.c_int]
ev_loop_new.restype = ctypes.POINTER(Loop)
ev_loop_destroy = dll.ev_loop_destroy
ev_loop_destroy.argtypes = [ctypes.POINTER(Loop)]
ev_loop_destroy.restype = None
ev_loop = dll.ev_loop
ev_loop.argtypes = [ctypes.POINTER(Loop), ctypes.c_int]
ev_loop.restype = None
ev_unloop = dll.ev_unloop
ev_unloop.argtypes = [ctypes.POINTER(Loop), ctypes.c_int]
ev_unloop.restype = None
ev_now = dll.ev_now
ev_now.argtypes = [ctypes.POINTER(Loop)]
ev_now.restype = ctypes.c_double
