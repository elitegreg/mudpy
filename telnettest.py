import socket

from socket import AF_INET6

from khakilet.hub import Hub
from khakilet.server import Listener
from khakilet.telnet import ConnectionClosed, Interrupt, LineTooLong, TelnetResponses, TelnetStream, Options, NoEcho

def handle_conn(conn, addr):
    ts = TelnetStream(conn)

    ts.request_window_size()
    ts.request_terminal_type()
    ts.enable_binary_mode()

    opts = ts.readoptions()

    if opts.term:
        ts.sendtext('Terminal Type = %s\n' % opts.term)
    if opts.window_size:
        ts.sendtext('Window Size = %s x %s\n' % opts.window_size)
    if ts.output_binary:
        ts.sendtext('Outputting binary\n')
    if ts.input_binary:
        ts.sendtext('Inputting binary\n')

    ts.sendtext('Username: ')
    username = ts.readline().rstrip()
    with NoEcho(ts):
      ts.sendtext('Password: ')
      password = ts.readline().rstrip()
      ts.sendtext('\n')

    while True:
      try:
        ts.sendtext('> ')
        line = ts.readline()
      except ConnectionClosed:
        print('Connection Closed')
        break
      except Interrupt:
        ts.sendtext('\nInterrupt\n')
        continue
      except LineTooLong:
        ts.sendtext('\nERROR: Command too long!\n')
        continue

      line = line.rstrip()
      print('Line = [%s]' % line)

      if line == 'foo':
        ts.sendtext('bar\n')
      elif line == 'bar':
        ts.sendtext('\u03a7\u03a6\n')
      elif line == 'exit':
        ts.close()
        return
      else:
        ts.sendtext('ERROR: Unknown Command\n')

if __name__ == '__main__':
    with Hub() as hub:
        hub.spawn(Listener(('', 31337), handle_conn, pf=AF_INET6).serve)
        hub.switch()

