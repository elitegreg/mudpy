import sys

PAGESIZE = 4096

if sys.platform == 'linux2':

  def statm():
    """Returns tuple of size in bytes: (total size, resident, share, text,
    lib, data)"""

    try:
      f = open('/proc/self/statm')
      results = f.readline().split(' ')
      total_size = int(results[0]) * PAGESIZE
      resident   = int(results[1]) * PAGESIZE
      shared     = int(results[2]) * PAGESIZE
      text       = int(results[3]) * PAGESIZE
      lib        = int(results[4]) * PAGESIZE
      data       = int(results[5]) * PAGESIZE
      return (total_size, resident, shared, text, lib, data)
    finally:
      f.close()

else:
  raise RuntimeError, "memory.py is only supported on linux"

