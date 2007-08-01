import sys
import telnetlib
import threading
import time
import unittest

from driver.TelnetServer import *
from reactor import reactor
from reactor.timed_event import Timed_Event

TEST_MSG = "This is a test\n"

class TelnetTestClient(threading.Thread):
  def __init__(self, host, port):
    threading.Thread.__init__(self)
    self.host = host
    self.port = port
    self.start()

  def run(self):
    tn = telnetlib.Telnet(self.host, self.port)
    t = tn.read_until('\n', 2)
    assert(t == TEST_MSG)
    tn.write(TEST_MSG)
    tn.close()


class TelnetServerTestCase(unittest.TestCase):
  def testTelnetServer(self):
    def handle_error(self):
      raise sys.exc_type, sys.exc_value

    TelnetConnection.handle_error = handle_error

    class Handler(object):
      def __init__(self):
        self.connected = 0
        self.disconnected = 0
        self.lines = list()

      def line_handler(self, line):
        self.lines.append(line)

      def connect_handler(self, conn):
        self.connected += 1
        conn.push(TEST_MSG)
        conn.line_handler.connect(self.line_handler)
        conn.disconnect_handler.connect(self.disconnect_handler)

      def disconnect_handler(self, conn):
        self.disconnected += 1
        reactor.stop_reactor()

    handler = Handler()

    server = TelnetServer(bindaddr='127.0.0.1', port=65000)
    server.connect_handler.connect(handler.connect_handler)

    client = TelnetTestClient('127.0.0.1', 65000)

    error = 0

    def timed_out(now):
      error = 1
      reactor.stop_reactor()

    Timed_Event.from_delay(timed_out, 5)

    reactor.start_reactor()
    reactor.close()

    client.join()

    self.assertEquals(error, 0)
    self.assertEquals(handler.connected, 1)
    self.assertEquals(handler.disconnected, 1)
    self.assertEquals(len(handler.lines), 1)
    self.assertEquals(handler.lines[0], TEST_MSG.rstrip())


if __name__ == '__main__':
  unittest.main()

