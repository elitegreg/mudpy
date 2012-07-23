from mudpy.driver import config

import io
import sys
import time
import traceback

_next_log_level = 0

class LogLevel:
    def __init__(self, level_name):
        global _next_log_level
        self.__level_name = level_name
        self.__level_value = _next_log_level
        _next_log_level += 1

    def __repr__(self):
        return self.__level_name

    def __lt__(self, x):
        return self.__level_value < x.__level_value

    def __le__(self, x):
        return self.__level_value <= x.__level_value

    def __eq__(self, x):
        return self.__level_value == x.__level_value

    def __ne__(self, x):
        return self.__level_value != x.__level_value

    def __ge__(self, x):
        return self.__level_value >= x.__level_value

    def __gt__(self, x):
        return self.__level_value > x.__level_value

FATAL = LogLevel('FATAL')
ERROR = LogLevel('ERROR')
WARN  = LogLevel('WARN')
INFO  = LogLevel('INFO')
DEBUG = LogLevel('DEBUG')
TRACE = LogLevel('TRACE')

def _level_from_string(loglevelstring):
    return globals()[loglevelstring]

CURRENT_LOG_LEVEL = _level_from_string(config.log.level)

try:
    LOGFILE = open(config.log.log_file, 'a')
except AttributeError:
    LOGFILE = sys.stdout

def _format_and_output(level, msg, *args, **kwargs):
    tm = time.time()
    ts = time.strftime(config.log.time_format, time.localtime(tm))
    if config.log.append_time_fraction:
        ts += config.log.append_time_fraction % (tm % 1)
    msg = msg.format(*args, **kwargs)
    print("{} [{}] - {}".format(tm, level, msg), file=LOGFILE)

def log(level, msg, *args, **kwargs):
    if CURRENT_LOG_LEVEL >= level:
        _format_and_output(level, msg, *args, **kwargs)

def fatal(msg, *args, **kwargs):
    return log(FATAL, msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    return log(ERROR, msg, *args, **kwargs)

def warn(msg, *args, **kwargs):
    return log(WARN, msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    return log(INFO, msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    return log(DEBUG, msg, *args, **kwargs)

def trace(msg, *args, **kwargs):
    if __debug__:
        return log(TRACE, msg, *args, **kwargs)
    return None

def exception(msg, *args, **kwargs):
    sio = io.StringIO()
    sio.write(msg)
    sio.write('\n')
    traceback.print_exception(*sys.exc_info(), file=sio)
    s = sio.getvalue()
    sio.close()
    error(s, *args, **kwargs)

