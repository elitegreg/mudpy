import asynchat
import asyncore
import logging
import socket
import telnetlib
import textwrap

from telnetlib import AO, AYT, BRK, DM, DO, DONT, ECHO, GA, IAC, \
                      IP, LINEMODE, NAWS, SB, SE, SGA, TM, TTYPE, \
                      WILL, WONT
from utils.SignalSlots import Signal

logger = logging.getLogger('TelnetServer')


class TelnetResponses:
  TELNET_BREAK_RESPONSE = IAC + WILL + TM
  TELNET_IP_RESPONSE    = IAC + WILL + TM
  TELNET_ABORT_RESPONSE = IAC + DM
  TELNET_DO_TM_RESPONSE = IAC + WILL + TM
  TELNET_DO_NAWS        = IAC + DO + NAWS
  TELNET_DO_TTYPE       = IAC + DO + TTYPE
  TELNET_TERM_QUERY     = IAC + SB + TTYPE + chr(1) + IAC + SE
  TELNET_WONT_ECHO      = IAC + WONT + ECHO
  TELNET_WILL_ECHO      = IAC + WILL + ECHO
  TELNET_WILL_SGA       = IAC + WILL + SGA
  TELNET_AYT_RESPONSE   = '\r\n[-Yes-]\r\n'
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

    self.__term_type = None
    self.__window_size = (80, 24)

    self.set_terminator('\n')
    
    self.__telnet_wrapper.option_callback.connect(self.__handle_option)

    # Reqeust Windows Size and Terminal Type
    self.push(TelnetResponses.TELNET_DO_NAWS)
    self.push(TelnetResponses.TELNET_DO_TTYPE)

  ### Properties ###

  @property
  def addr(self):
    return self.__addr

  @property
  def disconnect_handler(self):
    return self.__disconnect_handler

  @property
  def line_handler(self):
    return self.__line_handler

  @property
  def interrupt_handler(self):
    return self.__intr_handler

  @property
  def termtype(self):
    return self.__term_type

  @property
  def terminal_type_handler(self):
    return self.__term_type_handler

  @property
  def window_size(self):
    return self.__window_size

  @property
  def window_size_handler(self):
    return self.__window_size_handler

  ### End of Properties ###

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

  def wrapwrite(self, buf, newlines=0):
    width = self.window_size[0]
    nl = '\r\n' * newlines
    if len(buf) > width:
      msg = '\r\n'.join(textwrap.wrap(buf, width)) + nl
    else:
      msg = buf + nl
    self.push(msg)

  def __handle_option(self, sock, cmd, opt):
    if cmd == BRK:
      self.push(TelnetResponses.TELNET_BREAK_RESPONSE)
    elif cmd == IP:
      self.push(TelnetResponses.TELNET_IP_RESPONSE)
      self.__intr_handler()
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
      sbdata = self.read_sb_data()
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
        width = max(width, 10) # don't let the user make it too small
        height = max(height, 10) # don't let the user make it too small
        self.__window_size = (width, height)
        self.__window_size_handler()
      elif sbdata[0] == TTYPE:
        if sbdata[1] == 0:
          termtype = sbdata[2:]
        else:
          termtype = sbdata[1:]
        self.__term_type = termtype
        self.__term_type_handler(termtype)
      #else:
        # TODO Should callback here to pass suboptions
        #pass

  def connect_signals(self, obj):
    'Connects the signals to default functions on an object'

    disconnect = hasattr(obj, 'handle_disconnect')
    interrupt  = hasattr(obj, 'handle_interrupt')
    line       = hasattr(obj, 'handle_line')
    ttype      = hasattr(obj, 'handle_ttype')
    windowsize = hasattr(obj, 'handle_window_size')

    if disconnect:
      self.__disconnect_handler.connect(obj.handle_disconnect)
    if interrupt:
      self.__intr_handler.connect(obj.handle_interrupt)
    if line:
      self.__line_handler.connect(obj.handle_line)
    if ttype:
      self.__term_type_handler.connect(obj.handle_ttype)
    if windowsize:
      self.__window_size_handler.connect(obj.handle_window_size)

    if hasattr(obj, 'handle_telnet_connected'):
      obj.handle_telnet_connected()

  def disconnect_signals(self, obj):
    'Connects the signals to default functions on an object'

    disconnect = hasattr(obj, 'handle_disconnect')
    interrupt  = hasattr(obj, 'handle_interrupt')
    line       = hasattr(obj, 'handle_line')
    ttype      = hasattr(obj, 'handle_ttype')
    windowsize = hasattr(obj, 'handle_window_size')

    if disconnect:
      self.__disconnect_handler.disconnect(obj.handle_disconnect)
    if interrupt:
      self.__intr_handler.disconnect(obj.handle_interrupt)
    if line:
      self.__line_handler.disconnect(obj.handle_line)
    if ttype:
      self.__term_type_handler.disconnect(obj.handle_ttype)
    if windowsize:
      self.__window_size_handler.disconnect(obj.handle_window_size)


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

  ### Properties ###

  @property
  def connect_handler(self):
    return self.__connect_handler

  ### End of Properties ###

  def handle_accept(self):
    channel, addr = self.accept()
    logger.info('Connection From: %s', addr)
    conn = self.create_connection(channel, addr)
    self.__connect_handler(conn)

  def handle_error(self):
    logger.exception('handle_error()')

  def create_connection(self, channel, addr):
    return TelnetConnection(channel, addr)

