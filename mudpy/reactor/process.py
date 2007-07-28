import asynchat
import os
import popen_pid
import threading
import types

from reactor import file_dispatcher
from reactor import reactor


PIPE = popen_pid.PIPE
STDOUT = popen_pid.STDOUT


class WaitForCloseMixin(object):
  def __init__(self):
    self.closed_ = False
    self.closed_alert_ = threading.Condition()

  def wait_for_close(self):
    self.closed_alert_.acquire()
    try:
      while not self.closed_:
        self.closed_alert_.wait()
    finally:
      self.closed_alert_.release()

  def close_hook(self):
    self.closed_alert_.acquire()
    try:
      self.closed_ = True
      self.closed_alert_.notifyAll()
    finally:
      self.closed_alert_.release()


class _Read_Dispatcher(file_dispatcher, WaitForCloseMixin):
  def __init__(self, fd, handle_method):
    file_dispatcher.__init__(self, fd)
    WaitForCloseMixin.__init__(self)
    self.handle_read = handle_method

  def close(self):
    self.close_hook()
    return file_dispatcher.close(self)

  def handle_close(self):
    self.close()

  def writable(self):
    return False


class _Write_Dispatcher(file_dispatcher, WaitForCloseMixin):
  ac_out_buffer_size      = 4096

  def __init__ (self, fd):
    file_dispatcher.__init__(self, fd)
    WaitForCloseMixin.__init__(self)
    self.ac_out_buffer = ''
    self.producer_fifo = asynchat.fifo()
  
  def close(self):
    self.close_hook()
    return file_dispatcher.close(self)

  def handle_close(self):
    self.close()

  def readable(self):
    return False

  def refill_buffer (self):
    while 1:
      if len(self.producer_fifo):
        p = self.producer_fifo.first()
        # a 'None' in the producer fifo is a sentinel,
        # telling us to close the channel.
        if p is None:
          if not self.ac_out_buffer:
            self.producer_fifo.pop()
            self.close()
          return
        elif isinstance(p, str):
          self.producer_fifo.pop()
          self.ac_out_buffer = self.ac_out_buffer + p
          return
        data = p.more()
        if data:
          self.ac_out_buffer = self.ac_out_buffer + data
          return
        else:
          self.producer_fifo.pop()
      else:
        return

  def initiate_send (self):
    obs = self.ac_out_buffer_size
    # try to refill the buffer
    if (len (self.ac_out_buffer) < obs):
      self.refill_buffer()

    if self.ac_out_buffer and self.connected:
      # try to send the buffer
      try:
        num_sent = self.send (self.ac_out_buffer[:obs])
        if num_sent:
          self.ac_out_buffer = self.ac_out_buffer[num_sent:]

      except socket.error, why:
        self.handle_error()
        return

  def handle_write(self):
    self.initiate_send()

  def writable(self):
    return not (self.producer_fifo.is_empty() and self.connected)

  def push (self, data):
    self.producer_fifo.push(asynchat.simple_producer (data))
    self.initiate_send()

  def close_when_done(self):
    self.producer_fifo.push(None)


class Process(threading.Thread):
  'A process abstraction.'

  def __init__(self):
    threading.Thread.__init__(self)
    self.pid_ = None
    self.stdin = None
    self.stdout = None
    self.stderr = None

  def popen(self, args, stdin=None, stdout=None, stderr=None,
      close_fds=False, shell=False, cwd=None, env=None):
    obj = popen_pid.Popen(args, stdin, stdout, stderr, close_fds, shell,
        cwd, env)
    self.register(obj.pid, obj.stdin, obj.stdout, obj.stderr)

  def register(self, pid, stdin = None, stdout = None, stderr = None):
    self.pid_ = pid

    if stdin:
      if type(stdin) != types.IntType:
        stdin = stdin.fileno()
      self.stdin = _Write_Dispatcher(stdin)
    if stdout:
      if type(stdout) != types.IntType:
        stdout = stdout.fileno()
      self.stdout = _Read_Dispatcher(stdout, self.handle_stdout)
    if stderr:
      if type(stderr) != types.IntType:
        stderr = stderr.fileno()
      self.stderr = _Read_Dispatcher(stderr, self.handle_stderr)

    self.start()

  def run(self):
    (pid, status) = os.waitpid(self.pid_, 0) 
    if self.stdin:
      self.stdin.wait_for_close()
    if self.stdout:
      self.stdout.wait_for_close()
    if self.stderr:
      self.stderr.wait_for_close()
    reactor.notify(lambda: (self.join(), self.handle_exit(status)))

