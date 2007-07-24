import datetime
import os
import sys
import unittest

import reactor
import timed_event

def to_ms(delta):
  return delta.seconds * 1000000 + delta.microseconds

class TimerTestCase(unittest.TestCase):
  def setUp(self):
    self.times_ = list()
    self.count_ = 0
    self.interval_ = 0

  def testOneSecondInterval(self):
    count = 5
    self.times_ = list()
    self.times_.append(datetime.datetime.now())
    self.count_ = count
    self.interval_ = 1
    timed_event.Timed_Event.from_delay(self, 1)
    reactor.reactor.start_reactor()
    reactor.reactor.close()
    self.assertEquals(len(self.times_)-1, count)
    times = self.times_
    msecs = list()
    for i in xrange(0, count):
      msecs.append(to_ms(times[i+1]-times[i]))
    for m in msecs:
      self.failIf(m > 1010000 or m < 990000, "Microseconds not near 1 second: %d" % m)

  def testTwoSecondInterval(self):
    count = 3
    self.times_ = list()
    self.times_.append(datetime.datetime.now())
    self.count_ = count
    self.interval_ = 2
    timed_event.Timed_Event.from_delay(self, 2)
    reactor.reactor.start_reactor()
    reactor.reactor.close()
    self.assertEquals(len(self.times_)-1, count)
    times = self.times_
    msecs = list()
    for i in xrange(0, count):
      msecs.append(to_ms(times[i+1]-times[i]))
    for m in msecs:
      self.failIf(m > 2010000 or m < 1990000, "Microseconds not near 2 second: %d" % m)

  def testXTimerNoInterval(self):
    class Handler:
      def __init__(self):
        self.count = 0
      def handle_timer(self, now):
        self.count += 1

    handler = Handler()
    self.count_ = 1
    self.times_ = list()
    self.interval_ = 1
    timed_event.Timed_Event.from_delay(handler, 1)
    timed_event.Timed_Event.from_delay(self, 5)
    reactor.reactor.start_reactor()
    reactor.reactor.close()
    self.assertEquals(handler.count, 1)
    self.assertEquals(len(self.times_), 1)

  def handle_timer(self, now):
    self.times_.append(now)
    self.count_ -= 1
    if self.count_ <= 0:
      reactor.reactor.stop_reactor()
    return self.interval_


if __name__ == '__main__':
  unittest.main()

