import reactor
import unittest

class NotifyTestCase(unittest.TestCase):
  def testNotify(self):
    self.count = 0
    def incr():
      self.count += 1
      if self.count < 5:
        reactor.reactor.notify(lambda: incr())
      else:
        reactor.reactor.stop_reactor()
    reactor.reactor.notify(lambda: incr())
    reactor.reactor.start_reactor()
    reactor.reactor.close()

    self.assertEquals(self.count, 5)


if __name__ == '__main__':
  unittest.main()
