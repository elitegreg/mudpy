from mudpy import config

import contextlib
import enum
import io
import operator
import sys
import time
import traceback


class LogLevel(enum.Enum):
    FATAL = 0
    ERROR = 1
    WARN  = 2
    INFO  = 3
    DEBUG = 4
    TRACE = 5

    def __comparison__(self, rhs, op):
        return type(self) is type(rhs) and op(self.value, rhs.value)

    def __le__(self, rhs):
        return self.__comparison__(rhs, op=operator.le)

    def __lt__(self, rhs):
        return self.__comparison__(rhs, op=operator.lt)

    def __eq__(self, rhs):
        return self.__comparison__(rhs, op=operator.eq)

    def __ne__(self, rhs):
        return self.__comparison__(rhs, op=operator.ne)

    def __gt__(self, rhs):
        return self.__comparison__(rhs, op=operator.gt)

    def __ge__(self, rhs):
        return self.__comparison__(rhs, op=operator.ge)

    def __repr__(self):
        return 'LogLevel.{}={}'.format(self.name, self.value)

    def __str__(self):
        return self.name

def set_log_level(loglevelstring):
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = LogLevel[loglevelstring]

set_log_level(config.log.level)

@contextlib.contextmanager
def initialize(filename=None, fp=None):
    global LOGFILE
    if filename and fp:
        raise RuntimeError('Filename and fp cannot be specified at the same time!')
    elif filename:
        LOGFILE = open(filename, 'a')
    elif fp:
        LOGFILE = fp
    else:
        LOGFILE = sys.stdout
    yield
    LOGFILE.close()

def _format_and_output(level, msg, *args, **kwargs):
    tm = time.time()
    ts = time.strftime(config.log.time_format, time.localtime(tm))
    if config.log.append_time_fraction:
        ts += config.log.append_time_fraction % (tm % 1)
    msg = msg.format(*args, **kwargs)
    print("{} [{}] - {}".format(tm, str(level), msg), file=LOGFILE)

def log(level, msg, *args, **kwargs):
    if CURRENT_LOG_LEVEL >= level:
        _format_and_output(level, msg, *args, **kwargs)

def fatal(msg, *args, **kwargs):
    return log(LogLevel.FATAL, msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    return log(LogLevel.ERROR, msg, *args, **kwargs)

def warn(msg, *args, **kwargs):
    return log(LogLevel.WARN, msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    return log(LogLevel.INFO, msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    return log(LogLevel.DEBUG, msg, *args, **kwargs)

def trace(msg, *args, **kwargs):
    if __debug__:
        return log(LogLevel.TRACE, msg, *args, **kwargs)
    return None

def exception(msg, log_level=error, *args, **kwargs):
    sio = io.StringIO()
    sio.write(msg)
    sio.write('\n')
    traceback.print_exception(*sys.exc_info(), file=sio)
    s = sio.getvalue()
    sio.close()
    log_level(s, *args, **kwargs)

