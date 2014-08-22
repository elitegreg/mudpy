import io
import unittest

from mudpy import logging


class LoggingTests(unittest.TestCase):
    def test_set_log_level(self):
        for level in 'TRACE DEBUG INFO WARN ERROR FATAL'.split():
            logging.set_log_level(level)
            self.assertTrue(logging.CURRENT_LOG_LEVEL is getattr(logging.LogLevel, level))

    def test_log_levels(self):
        for loglevel in 'TRACE DEBUG INFO WARN ERROR FATAL'.split():
            levels = 'TRACE DEBUG INFO WARN ERROR FATAL'.split()
            data = io.StringIO()
            with logging.initialize(fp=data):
                logging.set_log_level(loglevel)
                for level in levels:
                    getattr(logging, level.lower())('test')
                expect_levels = levels[levels.index(loglevel):]
                for line in io.StringIO(data.getvalue()):
                    expected = expect_levels.pop(0)
                    self.assertTrue('[{}] - test'.format(expected) in line)


if __name__ == '__main__':
  unittest.main()
