import os
import process
import reactor
import unittest

class MyProc(process.Process):
  def __init__(self, output, input_cb, exit_cb):
    process.Process.__init__(self)
    self.output_ = output
    self.input_cb_ = input_cb
    self.exit_cb_ = exit_cb

  def popen(self, *args, **kwargs):
    process.Process.popen(self, *args, **kwargs)
    if self.output_:
      self.stdin.push(self.output_)
      self.stdin.close_when_done()

  def handle_stdout(self):
    buf = self.stdout.recv(4096)
    if buf:
      self.input_cb_(buf)

  def handle_exit(self, exit_status):
    self.exit_cb_(exit_status)
    reactor.reactor.stop_reactor()


class ProcessTestCase(unittest.TestCase):
  HELLO_WORLD = 'Hello World'
  THREE_LINES = 'This\nis\na test\n'

  def testCatProcess(self):
    proc = MyProc(ProcessTestCase.HELLO_WORLD, self.expectHelloWorld,
        lambda status: self.expectExitStatus(0, status))
    proc.popen(['cat'], stdin=process.PIPE, stdout=process.PIPE)

    reactor.reactor.start_reactor()
    reactor.reactor.close()

  def testGrepProcess(self):
    proc = MyProc(None, None, lambda status: self.expectExitStatus(2, status))
    proc.popen(['grep'], stderr=file('/dev/null', 'w'))

    reactor.reactor.start_reactor()
    reactor.reactor.close()

  def testWcProcess(self):
    proc = MyProc(ProcessTestCase.THREE_LINES, self.expectThree,
        lambda status: self.expectExitStatus(0, status))
    proc.popen(['wc', '-l'], stdin=process.PIPE, stdout=process.PIPE)

    reactor.reactor.start_reactor()
    reactor.reactor.close()

  def expectHelloWorld(self, str):
    self.assertEquals(str, ProcessTestCase.HELLO_WORLD)

  def expectThree(self, str):
    self.assertEquals(int(str), ProcessTestCase.THREE_LINES.count('\n'))

  def expectExitStatus(self, expect, status):
    self.assertEquals(os.WEXITSTATUS(status), expect)


if __name__ == '__main__':
  unittest.main()
