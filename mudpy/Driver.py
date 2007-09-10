import ConfigParser
import datetime
import logging
import optparse
import os
import signal
import sys
import threading
import utils.SignalSlots

from driver.Connections import ConnectionManager
from driver.ObjectAllocator import ObjectAllocator
from driver.stats import HeartbeatStats

from reactor import reactor
from reactor import timed_event


SHUTDOWN_SIGNALS = [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]

DRIVER = None
SINGLETON_LOCK = threading.RLock()


def driver(config):
  global DRIVER
  if DRIVER is None:
    if config is None:
      raise RuntimeError, "Driver isn't created yet, so driver(config) must be called!"
    SINGLETON_LOCK.acquire()
    try:
      if DRIVER is None:
        DRIVER = Driver(config)
    finally:
      SINGLETON_LOCK.release()
  return DRIVER


class Config(object):
  def __init__(self, configfile):
    self.__logger = logging.getLogger('Config')
    parser = ConfigParser.SafeConfigParser()
    parser.read(configfile)
    self.__config = dict()
    for section in parser.sections():
      section_dict = self.__config.setdefault(section,
          dict(parser.items(section)))

  def get(self, section, key, default=None, cast=None):
    retval = default

    section_dict = self.__config.get(section)

    if section_dict:
      value = section_dict.get(key)
      if value:
        retval = value
        if cast:
          retval = cast(retval)

    self.__logger.debug('get(%s, %s, %s) = %s', section, key,
      default, retval)

    return retval
    

class Driver(ObjectAllocator):
  def __init__(self, config):
    if config is None:
      raise RuntimeError, "Configuration not loaded. Driver can't be created!"

    ObjectAllocator.__init__(self, config)

    self.__logger = logging.getLogger('Driver')
    self.__config = config
    self.__load_time = datetime.datetime.now()
    self.__last_hb = self.__load_time

    self.__hb_stats = None
    hb_stat_time = self.__config.get('General', 'hb_stats', 0, int)
    if hb_stat_time > 0:
      self.__hb_stats = HeartbeatStats(hb_stat_time)

    self.__heartbeat = utils.SignalSlots.Signal()

    self.__logger.debug('Registering quit signals: %s',
        SHUTDOWN_SIGNALS)
    for sig in SHUTDOWN_SIGNALS:
      signal.signal(sig, self.__signal_handler)

  db = property(lambda self: self.__db)
  heartbeat_signal = property(lambda self: self.__heartbeat)

  def __signal_handler(self, signo, stackframe):
    if signo in SHUTDOWN_SIGNALS:
      reactor.notify(self.shutdown)

  def run(self):
    self.__logger.info('Starting services...')
    
    self.__logger.info('  Database...')
    self.__db = Database(self.__config.get('DB', 'file'))

    self.__logger.info('  ConnectionManager...')
    self.__conn_mgr = ConnectionManager(self.__config, self.__db)

    self.__heartbeat_interval = self.__config.get('General',
        'heartbeat_interval', 1, float)
    self.__logger.info('  Heartbeat...')
    timed_event.Timed_Event.from_delay(self.heartbeat, self.__heartbeat_interval)

    self.__logger.info('Starting event loop...')
    reactor.start_reactor()
    self.__logger.info('Closing event loop...')
    reactor.close()

  def shutdown(self):
    reactor.stop_reactor()

  def heartbeat(self, now):
    self.__last_hb = now 
    self.__logger.debug('Heartbeat: %s', now)
    self.__heartbeat()
    if self.__hb_stats:
      self.__hb_stats.add(now)
    return self.__heartbeat_interval


if __name__ == '__main__':
  DRIVER_DIR = os.path.dirname(sys.argv[0])
  if len(DRIVER_DIR) > 0:
    os.chdir(DRIVER_DIR)

  parser = optparse.OptionParser()
  parser.add_option('-c', '--config', dest='configfile',
      default='./etc/default.cfg',
      help='configuration filename')

  (options, args) = parser.parse_args()

  if len(args) > 0:
    parser.error('Too many arguments')

  logger = logging.getLogger()

  try:
    try:
      logger.info('Loading Game Config...')
      config = Config(options.configfile)
      
      logger.info('Starting Game Driver...')
      driver(config).run()
    except:
      logger.exception('Exception Caught at Top-Level, exiting')
      sys.exit(1)
  finally:
    logger.info('Exiting Game...')

  del DRIVER
  del config

  sys.exit(0)

