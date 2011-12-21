#!/usr/bin/env python
import sys

from ConfigParser import SafeConfigParser
from coverage import the_coverage


if __name__ == '__main__':
  if len(sys.argv) > 1:
    print >> sys.stderr, "Too many arguements"
    sys.exit(1)

  parser = SafeConfigParser()
  if len(parser.read('tools/coverage_tests.ini')) == 0:
    print >> sys.stderr, "No coverage_tests.ini file found"
    sys.exit(1)

  the_coverage.get_ready()

  retval = 0

  for file_name in parser.sections():
    _, statements, exclude, missing, readable = the_coverage.analysis2(file_name)
    the_coverage.annotate_file(file_name, statements, exclude, missing)
    n = len(statements)
    m = n - len(missing)
    if n > 0:
      pc = 100.0 * m / n
    else:
      pc = 100.0

    expected_pc = parser.getfloat(file_name, 'percentage')

    if pc < expected_pc:
      retval = 1
      print >> sys.stderr, \
          "Coverage %% of %s unexpected, got %s, expected %s" % \
          (file_name, pc, expected_pc)

  sys.exit(retval)
