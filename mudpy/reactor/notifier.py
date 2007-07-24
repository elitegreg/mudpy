import asyncore
import os
import Queue

class NotificationQueue(asyncore.file_dispatcher):
  def __init__(self):
    (self.rfd_, self.wfd_) = os.pipe()
    asyncore.file_dispatcher.__init__(self, self.rfd_)
    self.queue_ = Queue.Queue()

  def __call__(self, obj):
    self.queue_.put(obj)
    os.write(self.wfd_, "N")

  def writable(self):
    return False

  def handle_close(self):
    if self.rfd_:
      os.close(self.rfd_)
    if self.wfd_:
      os.close(self.wfd_)
    self.rfd_ = None
    self.wfd_ = None

  def handle_read(self):
    self.recv(512)
    while self.queue_.qsize() > 0:
      fun = self.queue_.get()
      fun()

