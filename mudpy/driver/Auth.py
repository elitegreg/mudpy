import bsddb
import shelve
import signals

from AuthStates import *
from reactor import timed_event


class AuthSession(object):
  def __init__(self, auth_daemon, conn, max_tries, timeout):
    self.__auth_daemon = auth_daemon
    self.__conn = conn
    self.__tries = max_tries
    self.__timeout = timeout
    self.__state = LoginPrompt(self, conn)
    self.__timer = timed_event.Timed_Event.from_delay(self, timeout)

    conn.connect_signals(self)

  @property
  def tries(self):
    return self.__tries

  def decrement_tries(self):
    self.__tries -= 1

  def handle_disconnect(self, conn):
    if self.__timer:
      self.__timer.cancel()

    # this should decrement ref count and delete the AuthSession:
    self.__auth_daemon.done_auth(self.__conn)

  def handle_interrupt(self):
    self.__timer += self.__timeout
    self.__state = LoginPrompt(self, self.__conn)

  def handle_line(self, line):
    self.__timer += self.__timeout
    newstate = None

    try:
      newstate = self.__state.handle_line(line)
    except AuthComplete: 
      pass

    if newstate is None:
      self.__auth_daemon.done_auth(self.__conn)
    else:
      self.__state = newstate

  def handle_timeout(self, now):
    self.__conn.push('Timeout....\n')
    self.__conn.close_when_done()
    self.__auth_daemon.done_auth(self.__conn)


class AuthDaemon(object):
  def __init__(self, max_tries=3, timeout=30):
    self.__tries = max_tries
    self.__timeout = timeout
    self.__auths = dict()

  def auth(self, conn):
    self.__auths[conn] = AuthSession(self, conn, self.__tries, self.__timeout)

  def done_auth(self, conn):
    auth = self.__auths.pop(conn, None)

