import sys
from functools import partial

import greenlet
from . import lib

Nothing = object()

class Branch(greenlet.greenlet):
    __slots__ = ('hub', '_run')

    def __init__(self, *args, hub, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub = hub

class Hub(greenlet.greenlet):

    def __init__(self, default_signals=None, **kwargs):
        if default_signals is None:
            self.default_signals = sys.platform != 'win32'
        else:
            self.default_signals = default_signals
        super().__init__(**kwargs)

    def spawn(self, fun, *args, **kw):
        watch = lib.Idle()
        watch.branch = Branch(partial(fun, *args, **kw), hub=self, parent=self)
        self.add_watch(watch)

    def _spawn(self):
        lib.Idle().start()

    def stop(self):
        lib.ev_unloop(self.handle, lib.EVUNLOOP_ONE);

    def run(self):
        lib.ev_loop(self.handle, 0)
        if hasattr(self, '_exception'):
            raise self._exception

    def sigint(self):
        import signal
        lib.Signal(signal.SIGINT).start()
        self._exception = KeyboardInterrupt()
        self.stop()

    def __enter__(self):
        self.handle = lib.ev_loop_new(0)
        self._children = {}
        if self.default_signals:
            self.spawn(self.sigint)
        return self

    def __exit__(self, A, B, C):
        lib.ev_loop_destroy(self.handle)
        del self.handle

    def add_watch(self, watch, value=Nothing, single=True, start=True):
        self._children[lib.ctypes.addressof(watch)] = watch
        watch._callback = lib.ev_callback(self.startsingle
            if single else self.startmulti)
        if value is Nothing:
            watch.value = ()
        else:
            watch.value = (value,)
        if start:
            watch.start_function(self.handle, watch)

    def remove_watch(self, watch):
        self._children.pop(lib.ctypes.addressof(watch))
        watch.stop_function(self.handle, watch)

    def startsingle(self, loop, ptr, event):
        try:
            watch = self._children.pop(ptr)
            watch.stop_function(loop, watch)
            branch = watch.branch
            val = watch.value
            del watch
            branch.switch(*val)
        except BaseException as e:
            sys.excepthook(*sys.exc_info())
            self._exception = e
            self.stop()

    def startmulti(self, loop, ptr, event):
        try:
            watch = self._children[ptr]
            branch = watch.branch
            val = watch.value
            del watch
            branch.switch(*val)
        except BaseException as e:
            sys.excepthook(*sys.exc_info())
            self._exception = e
            self.stop()


if __name__ == '__main__':
    while True:
        with Hub() as hub:
            hub.spawn(lambda: print('hello'))
            hub.switch()
