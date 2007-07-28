import asynchat
import asyncore
import logging
import socket
import telnetlib

from utils.SignalSlots import Signal

logger = logging.getLogger('TelnetServer')


class TelnetWrapper(telnetlib.Telnet):
  def __init__(self, sock):
    telnetlib.Telnet.__init__(self)
    self.sock = sock
    self.__option_callback = Signal()
    self.__option_callback.connect(self.__handle_option)
    self.set_option_negotiation_callback(self.__option_callback)

  def __getattr__(self, attr):
    return getattr(self.sock, attr)

  def recv(self, buffer_size):
    return self.read_very_eager()

  def send(self, data):
    return self.sock.send(data)

  def __handle_option(self, sock, cmd, opt):
    #logger.debug('__handle_option() addr=%s: cmd=%s, opt=%s',
        #self.sock.getpeername(), ord(cmd), ord(opt))
    if cmd in (telnetlib.DO, telnetlib.DONT):
      if opt == telnetlib.ECHO:
        return
      self.push(telnetlib.IAC + telnetlib.WONT + opt)
    elif cmd in (telnetlib.WILL, telnetlib.WONT):
      self.push(telnetlib.IAC + telnetlib.DONT + opt)


class TelnetConnection(asynchat.async_chat):
  def __init__(self, conn, addr):
    asynchat.async_chat.__init__(self, TelnetWrapper(conn))
    self.__addr = addr
    self.__disconnect_handler = Signal()
    self.__ibuffer = list()
    self.__line_handler = Signal()
    self.set_terminator('\n')

  addr = property(lambda self: self.__addr)
  disconnect_handler = property(lambda self: self.__disconnect_handler)
  line_handler = property(lambda self: self.__line_handler)

  def disable_local_echo(self):
    self.push(telnetlib.IAC + telnetlib.WILL + telnetlib.ECHO +
        telnetlib.IAC + telnetlib.GA)
  
  def enable_local_echo(self):
    self.push(telnetlib.IAC + telnetlib.WONT + telnetlib.ECHO)

  def recv(self, buffer_size):
    try:
      return self.socket.recv(buffer_size)
    except EOFError:
      self.handle_close()
      return ''
    except socket.error, why:
      # winsock sometimes throws ENOTCONN
      if why[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN]:
        self.handle_close()
        return ''
      else:
        raise

  def collect_incoming_data(self, data):
    self.__ibuffer.append(data)

  def found_terminator(self):
    line = ''.join(self.__ibuffer).rstrip('\r')
    self.__ibuffer = list()
    logger.debug('found_terminator() addr=%s: %s', self.__addr, line)
    self.__line_handler(line)

  def handle_error(self):
    logger.exception('handle_error() addr=%s', self.__addr)

  def close(self):
    logger.info('Disconnected: %s', self.__addr)
    self.__disconnect_handler(self)
    asynchat.async_chat.close(self)


class TelnetServer(asyncore.dispatcher):
  def __init__(self, bindaddr='', port=23):
    asyncore.dispatcher.__init__(self)
    self.__connect_handler = Signal()
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.set_reuse_addr()
    self.bind((bindaddr, port))
    self.listen(5)
    logger.debug('Bound and Listening (%s:%s)', bindaddr,
        port)

  connect_handler = property(lambda self: self.__connect_handler)

  def handle_accept(self):
    channel, addr = self.accept()
    logger.info('Connection From: %s', addr)
    conn = TelnetConnection(channel, addr)
    self.__connect_handler(conn)

  def handle_error(self):
    logger.exception('handle_error()')

