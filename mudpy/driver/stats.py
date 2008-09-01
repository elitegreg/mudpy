import collections
import logging

class HeartbeatStats(object):
  def __init__(self, stats_period=3600):
    self.__stats_period = stats_period
    self.__last_hb_time = None
    self.__values = collections.deque()

  def add(self, hb_time):
    if self.__last_hb_time:
      diff = hb_time - self.__last_hb_time
      diff = diff.seconds + diff.microseconds / 1000000.0
      self.__values.append(diff)

    self.__last_hb_time = hb_time

    while len(self.__values) > self.__stats_period:
      self.__values.popleft()

  def dump_stats(self):
    try:
      self.__values.sort()
      max_val = max(self.__values)
      min_val = min(self.__values)
      sum_val = sum(self.__values)
      cnt_val = len(self.__values)
      avg = 0
      percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
      p = [self.__values[cnt_val * x / 100] for x in percentiles]
      if cnt_val > 0:
        avg = sum_val / cnt_val
      stats = [cnt_val, avg, min_val, max_val]
      stats_msg = \
          "HeartbeatStats: %s data points\r\n" \
          "  avg: %s (sec)\r\n" \
          "  min: %s (sec)\r\n" \
          "  max: %s (sec)\r\n" + \
          '\r\n'.join(["  p%s: %s (sec)" % (p, v) for p, v in
            zip(percentiles, p)])
      logging.getLogger('Stats').info(stats_msg, *stats)
    except:
      pass

