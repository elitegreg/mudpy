from . import lib as ev, hub

import os


__all__ = [
    'Timer',
    'start_timer_service',
    'stop_timer_service',
]


class _Timer_Id():
    _value = 0

    @staticmethod
    def next():
        _Timer_Id._value += 1
        return _Timer_Id._value


class Timer:
    def __init__(self, callback, timeout, repeat=0.0):
        self.__timer_id = _Timer_Id.next()
        self.__towatch = ev.Timer(timeout, repeat)
        self.__cb = callback

        _timerservice.add_timer(self)

        _timerservice.hub.add_watch(
            self.__towatch, self.__timer_id, single=False)
        self.__towatch.branch = _timerservice
        self.__canceled = False

    @property
    def timer_id(self):
        return self.__timer_id

    def cancel(self):
        if not self.__canceled:
            self.__canceled = True
            _timerservice.cancel_timer(self)
            _timerservice.hub.remove_watch(self.__towatch)
            del self.__towatch.branch
            del self.__towatch

    def dispatch(self):
        self.__cb()
        if not self.__canceled and self.__towatch.repeat <= 0:
            self.cancel()


def start_timer_service(hub):
    global _timerservice
    _timerservice = _TimerService(hub)
    hub.spawn(_timerservice.switch)


def stop_timer_service():
    global _timerservice
    _timerservice.stop()
    _timerservice = None


class _TimerService(hub.Branch):
    def __init__(self, hub, **kwargs):
        super().__init__(hub=hub, **kwargs)
        self.__pipe = os.pipe()
        self.__iowatch = ev.Io(fd=self.__pipe[0], events=ev.EV_READ)
        self.__iowatch.branch = self
        self.__timers = dict()
        self.__running = True

    def add_timer(self, timer):
        self.__timers[timer.timer_id] = timer

    def cancel_timer(self, timer):
        self.__timers.pop(timer.timer_id)

    def run(self):
        self.hub.add_watch(self.__iowatch, 'io', single=False)

        try:
            while self.__running:
                timer_id = self.hub.switch()
                if timer_id == 'io':
                    os.read(self.__pipe[0], 64)
                else:
                    timer = self.__timers.get(timer_id)
                    if timer:
                        timer.dispatch()
        finally:
            self.hub.remove_watch(self.__iowatch)

        del self.__iowatch
        del self.__timers

        os.close(self.__pipe[0])
        os.close(self.__pipe[1])

    def stop(self):
        self.__running = False
        self.__notify()

        for timer in list(self.__timers.values()):
            timer.cancel()

    def __notify(self):
        os.write(self.__pipe[1], b'*')

