import asyncio
import errno

from socket import MSG_OOB

from telnetlib import AO, AYT, BINARY, BRK, DM, DO, DONT, ECHO, IAC, IP, \
    LINEMODE, NAWS, SB, SGA, SE, TTYPE, TM, WILL, WONT, theNULL

__all__ = [
    'LineTooLong',
    'ConnectionClosed',
    'Interrupt',
    'EOTRequested',
    'SenderTooFast',
    'NoEcho',
    'Options',
    'TelnetProtocol'
]

class LineTooLong(IOError): pass
class ConnectionClosed(IOError): pass
class Interrupt(IOError): pass
class EOTRequested(IOError): pass
class SenderTooFast(IOError): pass

class Options:
    def __init__(self):
        self.__term = "unknown"
        self.__ws   = (80, 24)

    @property
    def term(self):
        return self.__term

    @term.setter
    def term(self, value):
        self.__term = value

    @property
    def window_size(self):
        return self.__ws

    @window_size.setter
    def window_size(self, value):
        self.__ws = value

    def __repr__(self):
        return 'term=%s,window_size=%sx%s' % (
            self.term, self.window_size[0], self.window_size[1])


class _TelnetResponses:
    TELNET_BREAK_RESPONSE = IAC + WILL + TM
    TELNET_IP_RESPONSE    = IAC + WILL + TM
    TELNET_ABORT_RESPONSE = IAC + DM
    TELNET_DO_BINARY      = IAC + DO + BINARY
    TELNET_DONT_BINARY    = IAC + DONT + BINARY
    TELNET_DO_TM_RESPONSE = IAC + WILL + TM
    TELNET_DO_NAWS        = IAC + DO + NAWS
    TELNET_DO_TTYPE       = IAC + DO + TTYPE
    TELNET_TERM_QUERY     = IAC + SB + TTYPE + bytes([1]) + IAC + SE
    TELNET_WONT_ECHO      = IAC + WONT + ECHO
    TELNET_WILL_ECHO      = IAC + WILL + ECHO
    TELNET_WILL_SGA       = IAC + WILL + SGA
    TELNET_WILL_BINARY    = IAC + WILL + BINARY
    TELNET_WONT_BINARY    = IAC + WONT + BINARY
    TELNET_AYT_RESPONSE   = '\n[-Yes-]\n'
    TELNET_DONT_LINEMODE  = IAC + DONT + LINEMODE


class NoEcho:
    def __init__(self, telnetproto):
        self.__telnetproto = telnetproto

    def __enter__(self, *args, **kwargs):
        self.__telnetproto.echo = False

    def __exit__(self, *args, **kwargs):
        self.__telnetproto.echo = True


class TelnetProtocol(asyncio.Protocol):
    buffer_size = 1024
    inbound_q_size = 16
    binarycodec = 'utf8'
    endline = '\n'.encode(binarycodec)
    maxlinelen = 1024

    def __init__(self):
        self.__transport = None
        self.__rawq = b''
        self.__dataq = [b'', b'']
        self.__iacseq = b''
        self.__sb = 0
        self.__input_binary = False
        self.__output_binary = False
        self.__binary_requested = False
        self.__options = Options()
        self.__inbound_q = asyncio.Queue(TelnetProtocol.inbound_q_size)
        self.__echo = True

    def __getattr__(self, attr):
        return getattr(self.__transport, attr)

    @property
    def input_binary(self):
        return self.__input_binary

    @property
    def output_binary(self):
        return self.__output_binary

    @property
    def options(self):
        return self.__options

    @property
    def transport(self):
        return self.__transport

    @property
    def echo(self):
        return self.__echo

    @echo.setter
    def echo(self, echo):
        if echo:
            self.__echo = True
            self.send(_TelnetResponses.TELNET_WONT_ECHO)
        else:
            self.__echo = False
            self.send(_TelnetResponses.TELNET_WILL_ECHO)

    def close(self):
        if self.__transport:
            self.__transport.close()

    def connection_made(self, transport):
        self.__transport = transport

    def connection_lost(self, exc=None):
        self.__transport = None
        if exc is None:
            exc = ConnectionClosed()
        self.__inbound_q_put(exc)

    async def readline(self):
        line = await self.__inbound_q.get()
        if isinstance(line, IOError):
            raise line
        return line

    def data_received(self, data):
        self.__fill_queue(data)
        idx = self.__dataq[0].find(TelnetProtocol.endline)
        if idx >= 0:
            idx += len(TelnetProtocol.endline)
            res = self.__dataq[0][:idx]
            self.__dataq[0] = self.__dataq[0][idx:]
            if self.output_binary: # I don't understand this block?
                self.transport.write(b'\r')
            self.__inbound_q_put(res.decode(
                TelnetProtocol.binarycodec if self.__input_binary else 'ascii'))
                
        oldlen = len(self.__dataq[0])
        if TelnetProtocol.maxlinelen <= oldlen:
            self.close()
            self.__inbound_q_put(LineTooLong())

    def send(self, *args, **kwargs):
        if self.__transport:
            return self.__transport.write(*args, **kwargs)

    def sendtext(self, text, binarycodec='utf8'):
        if self.__transport:
            text = text.replace('\n', '\r\n')
            if self.__output_binary:
                buf = text.encode(
                    binarycodec, errors='replace').replace(IAC, IAC+IAC)
            else:
                buf = text.encode('ascii', errors='replace')
            return self.send(buf)

    def disable_binary_mode(self):
        self.send(_TelnetResponses.TELNET_WONT_BINARY)

    def enable_binary_mode(self):
        self.__binary_requested = True
        self.send(_TelnetResponses.TELNET_WILL_BINARY)
        self.send(_TelnetResponses.TELNET_DO_BINARY)
        
    def request_terminal_type(self):
        self.send(_TelnetResponses.TELNET_DO_TTYPE)

    def request_window_size(self):
        self.send(_TelnetResponses.TELNET_DO_NAWS)

    def __inbound_q_put(self, data):
        try:
            self.__inbound_q.put_nowait(data)
        except asyncio.QueueFull:
            self.close()
            asyncio.get_event_loop().create_task(self.__inbound_q.put(SenderTooFast('inbound queue full')))

    def __fill_queue(self, data):
        if not self.__rawq:
            self.__rawq = data
        else:
            self.__rawq += data

        try:
          for (i, c) in enumerate(self.__rawq):
              c = bytes([c])
              if not self.__iacseq:
                  if c not in (IAC, theNULL):
                      if ord(c) == 4: # ctrl-d EOF/EOT
                        self.__inbound_q_put(EOTRequested())
                      self.__dataq[self.__sb] += c
                  else:

                      if c == IAC:
                          self.__iacseq += c
                      continue
              elif len(self.__iacseq) == 1:
                  # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
                  if c in (DO, DONT, WILL, WONT):
                      self.__iacseq += c
                      continue

                  self.__iacseq = b''
                  if c == IAC:
                      self.__dataq[self.__sb] += c
                  else:
                      if c == SB: # SB ... SE start.
                          self.__sb = 1
                          self.__dataq[self.__sb] = b''
                      elif c == SE:
                          self.__sb = 0
                      self.__handle_option(c, self.__dataq[1])
              elif len(self.__iacseq) == 2:
                  cmd = self.__iacseq[1:2]
                  self.__iacseq = b''
                  if cmd in (DO, DONT):
                      self.__handle_option(cmd, c)
                  elif cmd in (WILL, WONT):
                      self.__handle_option(cmd, c)
        finally:
            self.__rawq = self.__rawq[i+1:]

    def __handle_option(self, cmd, opt):
        if cmd == BRK:
            self.send(_TelnetResponses.TELNET_BREAK_RESPONSE)
        elif cmd == IP:
            self.send(_TelnetResponses.TELNET_IP_RESPONSE)
            self.__inbound_q_put(Interrupt())
        elif cmd == AYT:
            self.send(_TelnetResponses.TELNET_AYT_RESPONSE)
        elif cmd == AO:
            self.sock.send(_TelnetResponses.TELNET_ABORT_RESPONSE, MSG_OOB)
        elif cmd == WILL:
            if opt == TTYPE:
                self.send(_TelnetResponses.TELNET_TERM_QUERY)
            elif opt == LINEMODE:
                self.send(_TelnetResponses.TELNET_DONT_LINEMODE)
            elif opt == ECHO or opt == NAWS:
                # do nothing, don't send DONT
                pass
            elif opt == BINARY:
                self.__input_binary = True
                if not self.__binary_requested:
                    self.send(_TelnetResponses.TELNET_DO_BINARY)
            else:
                self.send(IAC + DONT + opt)
        elif cmd == WONT:
            if opt == LINEMODE:
                self.send(_TelnetResponses.TELNET_DONT_LINEMODE)
            elif opt == BINARY:
                self.__input_binary = False
        elif cmd == DO:
            if opt == TM:
                self.send(_TelnetResponses.TELNET_DO_TM_RESPONSE)
            elif opt == SGA:
                self.send(_TelnetResponses.TELNET_WILL_SGA)
            elif opt == ECHO:
                # do nothing, don't send WONT
                pass
            elif opt == BINARY:
                self.__output_binary = True
                if not self.__binary_requested:
                    self.send(_TelnetResponses.TELNET_WILL_BINARY)
            else:
                self.send(IAC + WONT + opt)
        elif cmd == DONT:
            if opt == SGA:
                self.__inbound_q_push(
                    IOError('Client requested "DONT SGA": not supported'))
            elif opt == BINARY:
                self.__output_binary = False
        elif cmd == SE:
            cmd = bytes([opt[0]])
            if cmd == NAWS:
                if len(opt) == 5:
                    width = opt[1] << 16 + opt[2]
                    height = opt[3] << 16 + opt[4]
                elif len(opt) == 3:
                    width = opt[1]
                    height = opt[2]
                else:
                    width = 80
                    height = 24
                self.__options.window_size = (width, height)
            elif cmd == TTYPE:
                if opt[1] == 0:
                    termtype = opt[2:]
                else:
                    termtype = opt[1:]
                self.__options.term = termtype.decode()

