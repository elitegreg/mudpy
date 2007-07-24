import asyncore
import datetime
import heapq
import notifier
import threading
import time

dispatcher = asyncore.dispatcher
dispatcher_with_send = asyncore.dispatcher_with_send
file_dispatcher = asyncore.file_dispatcher


class Reactor(object):
  def __init__(self):
    self.notify             = notifier.NotificationQueue()
    self.running_           = False
    self.timers_            = list()
    self.call_when_running_ = list()

  running = property(lambda self: self.running_)

  def call_when_running(self, fun):
    if self.running_:
      raise Exception, \
        "call_when_running should not be called unless the reactor is running!"
    self.call_when_running_.append(fun)

  def close(self):
    asyncore.close_all()
    self.timers_            = list()
    self.notify             = notifier.NotificationQueue()
    self.call_when_running_ = list()

  def start_reactor(self, use_poll = False):
    self.running_ = True

    for fun in self.call_when_running_:
      fun()

    while self.running_:
      timeout = 30.0 # default 30 seconds before looping

      # check for timers
      if len(self.timers_) > 0:
        # get current time
        now = datetime.datetime.now()
        clock = time.time()
        # while the top of the heap is a timer for now or in the past
        while len(self.timers_) > 0 and \
            self.timers_[0].time <= now:
          # pop the top of the heap and call the handler
          event = heapq.heappop(self.timers_)
          event.handle_timer(now)
        if len(self.timers_) > 0:
          # there are still timers, so calculate how long until the next
          # one goes off in seconds
          nexttime = self.timers_[0].time
          timeout = nexttime - now
          timeout = timeout.seconds + (timeout.microseconds / 1000000.0)
          clockdiff = time.time() - clock
          timeout -= clockdiff # this should adjust for most of the time
                               # we spent in this block computing times

        # a timer handler may have stopped the reactor, check and break
        # if needed
        if self.running_ is False:
          break

      # run event loop once
      timeout = max(timeout, 0)
      asyncore.loop(timeout=timeout, use_poll=use_poll, count=1)

  def stop_reactor(self):
    self.running_ = False

  def _add_timed_event(self, event):
    '''This is an internal method used by Timed_Event'''
    heapq.heappush(self.timers_, event)

  def _remove_timed_event(self, event):
    '''This is an internal method used by Timed_Event'''
    try:
      self.timers_.remove(event)
      heapq.heapify(self.timers_)
    except ValueError:
      pass

  def _timed_event_change(self):
    '''This is an internal method used by Timed_Event'''
    heapq.heapify(self.timers_)


reactor = Reactor()

