from datetime import datetime
from datetime import timedelta
from reactor import timed_event


class AuthDaemon(object):
  def __init__(self, db, player_handler, conn, max_tries=3):
    self.__db = db
    self.__player_handler = player_handler
    self.__conn = conn
    self.__tries = max_tries
    self.__conn.line_handler.connect(self.handle_input)
    self.__conn.push('login: ')
    self.__store = dict()
    self.__state = AuthDaemon.login_state_handle_input
    self.__timeout = timed_event.Timed_Event.from_delay(
        self.timed_out, 10)

  def close(self):
    self.__conn.line_handler.disconnect(self.handle_input)
    self.__timeout.cancel()
    del self.__timeout

  def handle_input(self, inp):
    self.__timeout.set_delay(10)
    self.__state = self.__state(self, self.__conn, inp)
    if self.__state is None:
      login = self.__store['login']
      auth = self.__db.auth_user(login, self.__store['password'])
      if auth:
        self.close()
        self.__player_handler.user_authentication(True, self.__conn, login)
      else:
        if self.__tries == 1:
          self.close()
          self.__conn.push('Login failed, disconnecting...')
          self.__conn.close_when_done()
          self.__player_handler.user_authentication(False, self.__conn, login)
        else:
          self.__conn.push('Login failed, try again, login: ')
          self.__state = AuthDaemon.login_state_handle_input
          self.__tries -= 1

  def login_state_handle_input(self, conn, cmd):
    login = cmd.strip()
    self.__store['login'] = login.lower()
    conn.push("%s's password: " % login)
    conn.disable_local_echo()
    return AuthDaemon.password_state_handle_input

  def password_state_handle_input(self, conn, cmd):
    self.__store['password'] = cmd
    conn.enable_local_echo()
    return None

  def timed_out(self, now):
    self.close()
    self.__conn.push('Login timed out, disconnecting...')
    self.__conn.close_when_done()

