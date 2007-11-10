import asynchat
import errno
import Queue
import socket
import sys
import telnetlib
import threading
import time
import unittest
import weakref
import utils.hexdump

from driver.TelnetServer import *
from reactor import reactor
from reactor.timed_event import Timed_Event


C_MSG_LINE_1 = 'Hello World!\n'
C_MSG_LINE_2 = 'This is a test.\n'
C_OPT_BRK    = telnetlib.IAC + telnetlib.BRK
C_OPT_IP     = telnetlib.IAC + telnetlib.IP
C_OPT_AYT    = telnetlib.IAC + telnetlib.AYT
C_OPT_AO     = telnetlib.IAC + telnetlib.AO
C_WILL_TTYPE = telnetlib.IAC + telnetlib.WILL + telnetlib.TTYPE
C_WILL_LM    = telnetlib.IAC + telnetlib.WILL + telnetlib.LINEMODE
C_WILL_SGA   = telnetlib.IAC + telnetlib.WILL + telnetlib.SGA
C_WONT_LM    = telnetlib.IAC + telnetlib.WONT + telnetlib.LINEMODE
C_MSG_QUIT = 'QUIT\n'

S_MSG_LINE_1 = 'Yet another line\n'
S_MSG_LINE_2 = 'Test me\n'


class TelnetWrapper(telnetlib.Telnet):
  def __init__(self, host, port, option_callback=None):
    telnetlib.Telnet.__init__(self, host, port)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
    if option_callback:
      self.set_option_negotiation_callback(option_callback)

  def __getattr__(self, attr):
    return getattr(self.sock, attr)

  def recv(self, buffer_size):
    return self.read_very_eager()

  def send(self, data):
    return self.sock.send(data)


class TelnetClient(asynchat.async_chat):
  def __init__(self, host, port):
    self.telnet_wrapper = TelnetWrapper(host, port, self.handle_option)
    asynchat.async_chat.__init__(self, self.telnet_wrapper)
    self.__ibuffer = list()
    self.lines = list()
    self.options = list()
    self.set_terminator('\n')

  def recv(self, buffer_size):
    try:
      return self.socket.recv(buffer_size)
    except EOFError:
      self.handle_close()
      return ''
    except socket.error, why:
      # winsock sometimes throws ENOTCONN
      if why[0] in [errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN]:
        self.handle_close()
        return ''
      else:
        raise

  def collect_incoming_data(self, data):
    self.__ibuffer.append(data)

  def found_terminator(self):
    line = ''.join(self.__ibuffer).rstrip('\r')
    self.__ibuffer = list()
    self.lines.append(line)

  def handle_option(self, sock, cmd, opt):
    if cmd == telnetlib.SE:
      buf = self.telnet_wrapper.read_sb_data()
      self.options.append((cmd, opt, buf))
    else:
      self.options.append((cmd, opt))

  def handle_error(self):
    raise sys.exc_value

  def handle_expt(self):
    # recv oob data and discard, probably an ABORT
    pass


class TestableTelnetConnection(TelnetConnection):
  def handle_error(self):
    raise sys.exc_value


class TestableTelnetServer(TelnetServer):
  def handle_error(self):
    raise sys.exc_value

  def create_connection(self, channel, addr):
    return TestableTelnetConnection(channel, addr)


class TelnetServerTestCase(unittest.TestCase):
  class ConnHandler(object):
    def __init__(self, pushlist):
      self.pushlist = pushlist
      self.conn = None
      self.connproxy = None
      self.connects = 0
      self.disconnects = 0
      self.lines = list()
      self.ints = 0
      self.ttypes = 0
      self.ttype = None
      self.ws = 0
      self.width = 0
      self.height = 0

    def connect_handler(self, conn):
      self.conn = conn
      self.connproxy = weakref.ref(conn)
      self.connects += 1
      assert(self.conn.addr[0] == '127.0.0.1', 'Check addr property')
      conn.line_handler.connect(self.line_handler)
      conn.disconnect_handler.connect(self.disconnect_handler)
      conn.interrupt_handler.connect(self.interrupt_handler)
      conn.window_size_handler.connect(self.window_size_handler)
      conn.terminal_type_handler.connect(self.terminal_type_handler)
      conn.disable_local_echo()
      conn.enable_local_echo()
      for item in self.pushlist:
        conn.push(item)

    def disconnect_handler(self, conn):
      assert(conn == self.conn, 'Connection objects do not match')
      self.conn = None
      self.disconnects += 1
      reactor.stop_reactor()

    def line_handler(self, line):
      self.lines.append(line)
      if line == 'QUIT':
        self.conn.close_when_done()

    def interrupt_handler(self):
      self.ints += 1

    def terminal_type_handler(self, ttype):
      self.ttypes += 1
      self.ttype = ttype

    def window_size_handler(self):
      self.ws += 1
      self.window_size = self.conn.window_size


  def assertEquals(self, arg1, arg2, arg3 = ''):
    msg = '%s: [%s != %s]' % (arg3, arg1, arg2)
    super(TelnetServerTestCase, self).assertEquals(arg1, arg2, msg)

  def testTelnetServer(self):
    handler = TelnetServerTestCase.ConnHandler(
        [S_MSG_LINE_1, S_MSG_LINE_2])
    server = TestableTelnetServer(bindaddr='127.0.0.1', port=65000)
    server.connect_handler.connect(handler.connect_handler)

    client = TelnetClient('127.0.0.1', 65000)
    client.push(C_MSG_LINE_1)
    client.push(C_MSG_LINE_2)
    client.push(C_OPT_BRK)
    client.push(C_OPT_IP)
    client.push(C_OPT_AYT)
    client.push(C_OPT_AO)
    client.push(C_WILL_TTYPE)
    client.push(C_WILL_LM)
    client.push(C_WILL_SGA)
    client.push(C_WONT_LM)

    time_out = False

    def timed_out(now):
      time_out = True
      reactor.stop_reactor()

    Timed_Event.from_delay(timed_out, 0.2)

    def quit_conn(now):
      client.push(C_MSG_QUIT)

    Timed_Event.from_delay(quit_conn, 0.1)

    try:
      reactor.start_reactor()
      reactor.close()
    except Exception, e:
      print 'Exception:', e

    self.assertFalse(time_out, 'Test Timed Out ')

    self.assertEquals(handler.connects, 1)
    self.assertEquals(handler.disconnects, 1)

    self.assertEquals(len(handler.lines), 3,
        'Server Received Line Count (lines = %s)' % handler.lines)

    self.assertEquals(handler.lines[0], C_MSG_LINE_1.rstrip(),
        'Server Received Line 1')
    self.assertEquals(handler.lines[1], C_MSG_LINE_2.rstrip(),
        'Server Received Line 2')
    self.assertEquals(handler.lines[2], C_MSG_QUIT.rstrip(),
        'Server Received Line 3')

    self.assertEquals(len(client.lines), 4,
        'Client Received Line Count (lines = %s)' % client.lines)
    self.assertEquals(client.lines[0], S_MSG_LINE_1.rstrip(),
        'Client Received Line 1')
    self.assertEquals(client.lines[1], S_MSG_LINE_2.rstrip(),
        'Client Received Line 2')
    self.assertEquals(client.lines[2], '',
        'Client Received Line 3 (newline from AYT response)')
    self.assertEquals(client.lines[3], '[-Yes-]',
        'Client Received Line 4 (AYT response)')


    self.assertEquals(client.options[0], (telnetlib.DO, telnetlib.NAWS),
        'Client DO NAWS not received')
    self.assertEquals(client.options[1], (telnetlib.DO, telnetlib.TTYPE),
        'Client DO TTYPE not received')
    self.assertEquals(client.options[2], (telnetlib.WILL, telnetlib.ECHO),
        'Client WILL ECHO not received')
    self.assertEquals(client.options[3], (telnetlib.WONT, telnetlib.ECHO),
        'Client WONT ECHO not received')
    self.assertEquals(handler.ints, 1, 'Handler interrupts not fired')
    self.assertEquals(client.options[4], (telnetlib.WILL, telnetlib.TM),
        'Client WILL TM not received (from BRK/IP)')
    self.assertEquals(client.options[5], (telnetlib.WILL, telnetlib.TM),
        'Client WILL TM not received (from BRK/IP)')
    self.assertEquals(client.options[6], (telnetlib.DM, chr(0)),
        'Client DM not received')
    self.assertEquals(client.options[7], (telnetlib.SB, chr(0)),
        'Client SB (TTYPE HEADING) not received')
    self.assertEquals(client.options[8], (telnetlib.SE, chr(0),
        telnetlib.TTYPE + chr(1)), 'Client TTYPE not received')
    self.assertEquals(client.options[9], (telnetlib.DONT, telnetlib.LINEMODE),
        'Client DONT LINEMODE not received 1')
    self.assertEquals(client.options[10], (telnetlib.DONT, telnetlib.SGA),
        'Client DONT SGA not received')
    self.assertEquals(client.options[11], (telnetlib.DONT, telnetlib.LINEMODE),
        'Client DONT LINEMODE not received 2')
    self.assertEquals(handler.connproxy(), None,
        'Client connection object not garbage collected')


if __name__ == '__main__':
  unittest.main()

