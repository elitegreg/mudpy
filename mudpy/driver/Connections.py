import Auth
import logging

from TelnetServer import TelnetServer


logger = logging.getLogger('Connections')


class ConnectionManager(object):
  def __init__(self, config, db):
    self.__config = config
    self.__db = db
    self.__connections = dict()
    self.__auths = dict()

    self.__max_login_tries = self.__config.get('Auth', 'max_tries', 3,
        int)

    bindaddr = self.__config.get('Telnet', 'bind', '')
    port     = self.__config.get('Telnet', 'port', 12345, int)
    self.__telnet_server = TelnetServer(bindaddr, port,
        self.telnet_connect_handler, self.telnet_disconnect_handler)

  def telnet_connect_handler(self, conn):
    logger.info('Handling connect from %s', conn.addr)
    auth = Auth.AuthDaemon(self.__db, self, conn,
        self.__max_login_tries)
    self.__auths[conn] = auth

  def telnet_disconnect_handler(self, conn):
    logger.info('Handling disconnect from %s', conn.addr)
    auth = self.__auths.pop(conn, None)
    if auth:
      auth.close()

  def user_authentication(self, authenticated, conn, login=None):
    if authenticated:
      auth = self.__auths.pop(conn, None)
      logger.info('User authenticated: %s', login)
      conn.push('\n\nAuthentication successful...\n\n')
    else:
      logger.info('User authentication failed: %s', login)

