from . import lib as ev, hub

import os


class Timer_Id():
    _value = 0

    @staticmethod
    def next():
        Timer_Id._value += 1
        return Timer_Id._value


class Timer:
    def __init__(self, callback, timeout, repeat=0.0):
        self.__timer_id = Timer_Id.next()
        self.__towatch = ev.Timer(timeout, repeat)
        self.__cb = callback

        _timerservice.addTimer(self)

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
            _timerservice.cancelTimer(self)
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
    __slots__ = ('pipe', 'iowatch', 'greenlet', 'timers', 'running')

    def __init__(self, hub, **kwargs):
        super().__init__(hub=hub, **kwargs)
        self.pipe = os.pipe()
        self.iowatch = ev.Io(fd=self.pipe[0], events=ev.EV_READ)
        self.iowatch.branch = self
        self.hub.add_watch(self.iowatch, 'io', single=False)
        self.timers = dict()
        self.running = True

    def addTimer(self, timer):
        self.timers[timer.timer_id] = timer

    def cancelTimer(self, timer):
        self.timers.pop(timer.timer_id)

    def run(self):
        try:
            while self.running:
                timer_id = self.hub.switch()
                if timer_id == 'io':
                    os.read(self.pipe[0], 64)
                else:
                    timer = self.timers.get(timer_id)
                    if timer:
                        timer.dispatch()
        finally:
            self.hub.remove_watch(self.iowatch)

        del self.iowatch
        del self.timers

        os.close(self.pipe[0])
        os.close(self.pipe[1])

    def stop(self):
        self.running = False
        self.__notify()

        for timer in list(self.timers.values()):
            timer.cancel()

    def __notify(self):
        os.write(self.pipe[1], b'*')


if __name__ == '__main__':
    count = 0
    def cb2():
        print('cb2')
    def cb1():
        global count
        count += 1
        print('timer callback')
        if count == 5:
            print('scheduling another timer')
            timer3 = Timer(cb2, 0.2, 0.2)

    def end():
        stop_timer_service()
        hub.stop()

    from .hub import Hub
    with Hub() as hub:
        start_timer_service(hub)
        timer1 = Timer(cb1, 1.0, 1.0)
        timer2 = Timer(end, 10)
        hub.switch()

