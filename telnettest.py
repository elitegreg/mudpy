from khakilet.hub import Hub
from khakilet.server import Listener
from khakilet.telnet import ConnectionClosed, Interrupt, LineTooLong, TelnetResponses, TelnetStream, TerminalType, WindowSize

def handle_conn(conn, addr):
    ts = TelnetStream(conn)

    ts.send(TelnetResponses.TELNET_DO_NAWS)
    ts.send(TelnetResponses.TELNET_DO_TTYPE)

    while True:
      ts.send(b'> ')
      
      try:
        line = ts.readline()
      except ConnectionClosed:
        print('Connection Closed')
        break
      except Interrupt:
        ts.send(b'\nInterrupt\n')
        continue
      except LineTooLong:
        ts.send(b'\nERROR: Command too long!\n')
        continue
      except TerminalType as t:
        ts.send(('\nTerminal Type = %s\n' % t.term).encode())
        continue
      except WindowSize as w:
        ts.send(('\nWindow Size = %s x %s\n' % (w.width, w.height)).encode())
        continue

      line = line.rstrip().decode()
      print('Line = [%s]' % line)

      if line == 'foo':
        ts.send(b'bar\n')
      elif line == 'bar':
        ts.send(b'baz\n')
      elif line == 'exit':
        ts.close()
        return
      else:
        ts.send(b'ERROR: Unknown Command\n')

if __name__ == '__main__':
    with Hub() as hub:
        hub.spawn(Listener(('127.0.0.1', 31337), handle_conn).serve)
        hub.switch()

