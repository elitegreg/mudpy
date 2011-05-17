import Auth
import logging

from mudlib.loader import ObjectLoader as ObjectLoader
from TelnetServer import TelnetServer


logger = logging.getLogger('Connections')


class ConnectionManager(object):
  def __init__(self, config):
    self.__connections = dict()
    self.__auths = dict()

    self.__max_login_tries = config.get('Auth', 'max_tries', 3,
        int)

    bindaddr = config.get('Telnet', 'bind', '')
    port     = config.get('Telnet', 'port', 12345, int)
    self.__telnet_server = TelnetServer(bindaddr, port)
    self.__telnet_server.connect_handler.connect(self.telnet_connect_handler)

  def telnet_connect_handler(self, conn):
    logger.info('Handling connect from %s', conn.addr)
    conn.disconnect_handler.connect(self.telnet_disconnect_handler)
    auth = Auth.AuthDaemon((lambda login, password: True), self, conn,
        self.__max_login_tries)
    self.__auths[conn] = auth

  def telnet_disconnect_handler(self, conn):
    logger.info('Handling disconnect from %s', conn.addr)
    auth = self.__auths.pop(conn, None)
    player = self.__connections.pop(conn, None)
    if auth:
      auth.close()
    if player:
      player.disconnect()

  def user_authentication(self, authenticated, conn, login=None):
    auth = self.__auths.pop(conn, None)
    if authenticated:
      logger.info('User authenticated: %s', login)
      conn.push('\n\nAuthentication successful...\n\n')
      player = ObjectLoader.load_player(login)
      self.__connections[conn] = player
      player.add_connection(conn)
    else:
      conn.close_when_done()
      logger.info('User authentication failed: %s', login)

