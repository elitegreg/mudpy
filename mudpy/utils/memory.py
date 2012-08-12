"""
A module to get information about memory usage.
"""

import sys


if sys.platform.startswith('linux'):
  PAGESIZE = 4096 #: System page size

  def statm():
    """
    Get the memory usage for this process provided by /proc/self/statm.

    @rtype:  tuple
    @return: (total_size, resident, shared, text, lib, data) in bytes
    """

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
  raise RuntimeError("memory.py is only supported on linux")

