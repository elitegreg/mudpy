from datetime import datetime
from datetime import timedelta
from reactor import timed_event


DEFAULT_TIMEOUT = 30


class AuthDaemon(object):
  def __init__(self, check_pass_fun, conn_mgr, conn, max_tries=3):
    self.__check_pass_fun = check_pass_fun
    self.__conn_mgr = conn_mgr
    self.__conn = conn
    self.__tries = max_tries
    self.__conn.line_handler.connect(self.handle_input)
    self.__conn.push('login: ')
    self.__store = dict()
    self.__state = AuthDaemon.login_state_handle_input
    self.__timeout = timed_event.Timed_Event.from_delay(
        self.timed_out, DEFAULT_TIMEOUT)

  def close(self):
    self.__conn.line_handler.disconnect(self.handle_input)
    self.__timeout.cancel()
    del self.__timeout

  def handle_input(self, inp):
    self.__timeout.set_delay(DEFAULT_TIMEOUT)
    self.__state = self.__state(self, self.__conn, inp)
    if self.__state is None:
      login = self.__store['login']
      auth = self.__check_pass_fun.auth_user(login, self.__store['password'])
      if auth:
        self.close()
        self.__conn_mgr.user_authentication(True, self.__conn, login)
      else:
        if self.__tries == 1:
          self.close()
          self.__conn.push('Login failed...')
          self.__conn_mgr.user_authentication(False, self.__conn, login)
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
    self.__conn.push('Login timed out...')
    self.__conn_mgr.user_authentication(False, self.__conn, 'timeout')

