import asyncore
import reactor
import socket
import unittest

PORT=31337
MSG='This is a test message'


class MyServerChannel(asyncore.dispatcher_with_send):
  def handle_read(self):
    buf = self.recv(4096)
    if buf:
      self.send(buf)

class MyServer(asyncore.dispatcher):
  def __init__(self, port=PORT):
    asyncore.dispatcher.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.bind(("", port))
    self.listen(5)
    self.connections = 0

  def handle_accept(self):
    channel, addr = self.accept()
    self.connections += 1
    MyServerChannel(channel)

class MyClient(asyncore.dispatcher_with_send):
  instance_count = 0

  def __init__(self, host='127.0.0.1', port=PORT):
    asyncore.dispatcher_with_send.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connect((host, port))
    self.received_ = None
    MyClient.instance_count += 1

  def handle_connect(self):
    self.send(MSG)

  def handle_read(self):
    buf = self.recv(4096)
    if buf:
      self.received_ = buf
      MyClient.instance_count -= 1
      if MyClient.instance_count == 0:
        reactor.reactor.stop_reactor()

class SocketTestCase(unittest.TestCase):
  def testSockets(self):
    server = MyServer()
    client1 = MyClient()
    client2 = MyClient()

    reactor.reactor.start_reactor()
    reactor.reactor.close()

    self.assertEquals(server.connections, 2)
    self.assertEquals(client1.received_, MSG)
    self.assertEquals(client2.received_, MSG)

if __name__ == '__main__':
  unittest.main()

