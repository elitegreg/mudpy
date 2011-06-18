from . import lib as ev

from greenlet import getcurrent


class Timeout:
    def __init__(self, seconds):
        self.seconds = seconds

        if seconds and seconds >= 0.000000001:
          self.towatch = ev.Timer(seconds)
          self.towatch.branch = getcurrent()

    def __enter__(self):
        if self.seconds:
            getcurrent().hub.add_watch(self.towatch, 'khakilet timeout')
        return self

    def __exit__(self, typ, value, tb):
        pass
