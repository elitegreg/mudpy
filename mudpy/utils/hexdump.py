"""
This module provides an interface to pretty print binary data as
hexadecimal in ASCII.
"""

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.'
  for x in range(256)]) #: A translation filter for converting chars

def dump(src, length=16):
  N=0; result=''
  while src:
    s,src = src[:length],src[length:]
    hexa = ' '.join(["%02X"%ord(x) for x in s])
    s = s.translate(FILTER)
    result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
    N+=length
  return result
