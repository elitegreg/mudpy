import datetime
import reactor


class Timed_Event(object):
  @staticmethod
  def from_delay(handler, delay, reactor=reactor.reactor):
    if delay is None:
      raise TypeError, 'Timed_Event delay must be in numeric seconds or datetime.timedelta'
    if isinstance(delay, datetime.timedelta):
      time = datetime.datetime.now() + delay
    else:
      time = datetime.datetime.now() + datetime.timedelta(seconds=delay)
    return Timed_Event(handler, time, reactor)

  def __init__(self, handler, time=None, reactor=reactor.reactor):
    if reactor is None:
      raise Type_Error, 'Timed_Event reactor must not be None'
    if time and not isinstance(time, datetime.datetime):
      raise TypeError, 'Timed_Event time must be a datetime.datetime'
    self.reactor_ = reactor
    self.handler_ = handler
    if time:
      self.time_ = time
    else:
      self.time_ = datetime.datetime.now()
    reactor._add_timed_event(self)

  def __cmp__(self, rhs):
    return cmp(self.time_, rhs.time_)

  def __iadd__(self, x):
    if isinstance(x, datetime.timedelta):
      self.time_ += x
    else:
      self.time_ += datetime.timedelta(seconds=x)
    self.reactor_._timed_event_change()
    return self

  def __isub__(self, x):
    if isinstance(x, datetime.timedelta):
      self.time_ -= x
    else:
      self.time_ -= datetime.timedelta(seconds=x)
    self.reactor_._timed_event_change()
    return self

  def cancel(self):
    self.reactor_._remove_timed_event(self)

  def set_delay(self, delay):
    if isinstance(delay, datetime.timedelta):
      self.time_ = datetime.datetime.now() + delay
    else:
      self.time_ = datetime.datetime.now() + datetime.timedelta(seconds=delay)
    self.reactor_._timed_event_change()

  handler = property(lambda self: self.handler_)
  reactor = property(lambda self: self.reactor_)
  time = property(lambda self: self.time_)

  def handle_timer(self, now):
    handler_function = getattr(self.handler_, 'handle_timer',
        self.handler_)
    result = handler_function(now)
    if result:
      if isinstance(result, datetime.datetime):
        self.time_ = result
      else:
        self.time_ += datetime.timedelta(seconds=result)
      self.reactor_._add_timed_event(self)

