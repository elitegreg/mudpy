import errno
import os

def mkdir(dir):
  try:
    os.makedirs(dir)
  except OSError as e:
    if e.errno != errno.EEXIST or not os.path.isdir(dir):
      raise
