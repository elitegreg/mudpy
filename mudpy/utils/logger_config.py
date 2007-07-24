import logging.config
import os.path

LOG_CONFIG = './etc/logger.cfg'

if os.path.exists(LOG_CONFIG):
  logging.config.fileConfig(LOG_CONFIG)

