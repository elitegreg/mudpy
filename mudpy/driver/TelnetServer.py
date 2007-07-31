import asynchat
import asyncore
import logging
import socket
import telnetlib
import utils.hexdump

from telnetlib import AO, AYT, BRK, DM, DO, DONT, ECHO, GA, IAC, \
                      IP, LINEMODE, NAWS, SB, SE, SGA, TM, TTYPE, \
                      WILL, WONT
from utils.SignalSlots import Signal

logger = logging.getLogger('TelnetServer')


class TelnetResponses:
  TELNET_BREAK_RESPONSE = chr(28) + IAC + WILL + TM
  TELNET_IP_RESPONSE    = chr(127) + IAC + WILL + TM
  TELNET_ABORT_RESPONSE = IAC + DM
  TELNET_DO_TM_RESPONSE = IAC + WILL + TM
  TELNET_DO_NAWS        = IAC + DO + NAWS
  TELNET_DO_TTYPE       = IAC + DO + TTYPE
  TELNET_TERM_QUERY     = IAC + SB + TTYPE + chr(1) + IAC + SE
  TELNET_WONT_ECHO      = IAC + WONT + ECHO
  TELNET_WILL_ECHO      = IAC + WILL + ECHO
  TELNET_WILL_SGA       = IAC + WILL + SGA
  TELNET_AYT_RESPONSE   = '\n[-Yes-]\n'
  TELNET_DONT_LINEMODE  = IAC + DONT + LINEMODE


class TelnetWrapper(telnetlib.Telnet):
  def __init__(self, sock):
    telnetlib.Telnet.__init__(self)
    self.sock = sock
    self.option_callback = Signal()
    self.set_option_negotiation_callback(self.option_callback)

  def __getattr__(self, attr):
    return getattr(self.sock, attr)

  def recv(self, buffer_size):
    return self.read_very_eager()

  def send(self, data):
    return self.sock.send(data)


class TelnetConnection(asynchat.async_chat):
  def __init__(self, conn, addr):
    self.__telnet_wrapper = TelnetWrapper(conn)
    asynchat.async_chat.__init__(self, self.__telnet_wrapper)
    self.__addr = addr
    self.__disconnect_handler = Signal()
    self.__ibuffer = list()
    self.__line_handler = Signal()
    self.__intr_handler = Signal()
    self.__term_type_handler = Signal()
    self.__window_size_handler = Signal()
    self.set_terminator('\n')
    
    self.__telnet_wrapper.option_callback.connect(self.__handle_option)

    # Reqeust Windows Size and Terminal Type
    self.push(TelnetResponses.TELNET_DO_NAWS)
    self.push(TelnetResponses.TELNET_DO_TTYPE)

  addr = property(lambda self: self.__addr)
  disconnect_handler = property(lambda self: self.__disconnect_handler)
  line_handler = property(lambda self: self.__line_handler)
  interrupt_handler = property(lambda self: self.__intr_handler)
  terminal_type_handler = property(lambda self:
      self.__term_type_handler)
  window_size_handler = property(lambda self: self.__window_size_handler)

  def disable_local_echo(self):
    self.push(TelnetResponses.TELNET_WILL_ECHO)
  
  def enable_local_echo(self):
    self.push(TelnetResponses.TELNET_WONT_ECHO)

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

  def __handle_option(self, sock, cmd, opt):
    if cmd == BRK:
      self.push(TelnetResponses.TELNET_BREAK_RESPONSE)
    elif cmd == IP:
      self.__intr_handler()
      self.push(TelnetResponses.TELNET_IP_RESPONSE)
    elif cmd == AYT:
      self.push(TelnetResponses.TELNET_AYT_RESPONSE)
    elif cmd == AO:
      self.sock.send(TelnetResponses.TELNET_ABORT_RESPONSE,
          socket.MSG_OOB)
    elif cmd == WILL:
      if opt == TTYPE:
        self.push(TelnetResponses.TELNET_TERM_QUERY)
      elif opt == LINEMODE:
        self.push(TelnetResponses.TELNET_DONT_LINEMODE)
      elif opt == ECHO or opt == NAWS:
        # do nothing, don't send DONT
        pass
      else:
        self.push(IAC + DONT + opt)
    elif cmd == WONT:
      if opt == LINEMODE:
        self.push(TelnetResponses.TELNET_DONT_LINEMODE)
    elif cmd == DO:
      if opt == TM:
        self.push(TelnetResponses.TELNET_DO_TM_RESPONSE)
      elif opt == SGA:
        self.push(TelnetResponses.TELNET_WILL_SGA)
      elif opt == ECHO:
        # do nothing, don't send WONT
        pass
      else:
        self.push(IAC + WONT + opt)
    elif cmd == DONT:
      if opt == SGA:
        logger.info('Client requested "DONT SGA: not supported')
    elif cmd == SE:
      sbdata = self.sbdataq
      if sbdata[0] == NAWS:
        if len(sbdata) == 5:
          width = ord(sbdata[1]) << 16 + ord(sbdata[2])
          height = ord(sbdata[3]) << 16 + ord(sbdata[4])
        elif len(sbdata) == 3:
          width = ord(sbdata[1])
          height = ord(sbdata[2])
        else:
          width = 80
          height = 24
        self.__window_size_handler(width, height)
      elif sbdata[0] == TTYPE:
        if sbdata[1] == 0:
          termtype = sbdata[2:]
        else:
          termtype = sbdata[1:]
        self.__term_type_handler(termtype)
      #else:
        # TODO Should callback here to pass suboptions
        #pass


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

