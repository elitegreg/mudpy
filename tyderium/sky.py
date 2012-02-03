from collections import deque
from greenlet import getcurrent
from . import lib

class Condition(object):

    def __init__(self):
        self._consumers = deque()

    def wait(self):
        watch = lib.Idle()
        branch = watch.branch = getcurrent()
        branch.hub.add_watch(watch, start=False)
        self._consumers.append(watch)
        branch.hub.switch()

    def notify(self):
        if self._consumers:
            watch = self._consumers.popleft()
            watch.start_function(getcurrent().hub.handle, watch)

    def notifyall(self):
        handle = getcurrent().hub.handle
        for watch in self._consumers:
            # start_function just adds item into libev event loop
            # so we assume that ``wait()`` can't be called between iterations
            watch.start_function(handle, watch)
        self._consumers.clear()

class Queue(object):
    """Multiple producers multiple consumers queue."""

    class Stop(Exception):
        """Raised when trying to ``get()`` already ``close()``d queue"""

    class Closed(Exception):
        """Raised when trying to ``put()`` into already ``close()``d queue"""

    def __init__(self):
        self._queue = deque()
        self._condition = Condition()
        self._done = False

    def __iter__(self):
        try:
            while not self._done:
                yield self.get()
        except self.Stop:
            pass

    def get(self):
        while not self._queue and not self._done:
            self._condition.wait()
        if not self._queue:
            raise self.Stop()
        return self._queue.popleft()

    def getall(self):
        while not self._queue and not self._done:
            self._condition.wait()
        res = tuple(self._queue)
        self._queue.clear()
        if not res:
            raise self.Stop()
        return res

    def put(self, value):
        if self._done:
            raise self.Closed()
        self._queue.append(value)
        self._condition.notify()

    def close(self):
        self._done = True
        self._condition.notifyall()

    def __len__(self):
        return len(self._queue)
