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

def _format_and_output(level, msg):
    tm = time.time()
    ts = time.strftime(config.log.time_format, localtime(tm))
    if config.log.append_time_fraction:
        ts += config.log.append_time_fraction % (tm % 1)
    print("%s [%s] - %s" % (tm, level, msg), file=LOGFILE)

def log(level, msg, *args):
    if CURRENT_LOG_LEVEL >= level:
        _format_and_output(level, msg % args)

def fatal(msg, *args):
    return log(FATAL, msg, *args)

def error(msg, *args):
    return log(ERROR, msg, *args)

def warn(msg, *args):
    return log(WARN, msg, *args)

def info(msg, *args):
    return log(INFO, msg, *args)

def debug(msg, *args):
    return log(DEBUG, msg, *args)

def trace(msg, *args):
    if __debug__:
        return log(TRACE, msg, *args)
    return None

def exception(msg, *args):
    sio = io.StringIO()
    sio.write(msg)
    sio.write('\n')
    traceback.print_exception(*sys.exc_info(), None, sio)
    s = sio.getvalue()
    sio.close()
    error(s, *args)

