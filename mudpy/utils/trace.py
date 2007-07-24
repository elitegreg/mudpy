import sys
import traceback

def stacktrace(frames = 20):
  type, value, stack = sys.exc_info()
  formattedBacktrace = "".join (traceback.format_exception(type, value, stack, frames))
  return formattedBacktrace
