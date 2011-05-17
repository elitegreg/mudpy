import bsddb
import shelve
import signals
import utils.passwd_tool

from AuthStates import *
from reactor import timed_event


class PasswordDB(object):
  def __init__(self, passwd_file):
    super(PasswordDB, self).__init__()
    btree = bsddb.btopen(passwd_file)
    self.__db = shelve.BsdDbShelf(btree, protocol=2)

  def __contains__(self, user):
    return user in self.__db

  def compare(self, user, passwd):
    p = self.__db.get(user)
    if not p:
      raise KeyError('Password for user %s does not exist' % user)
    return utils.passwd_tool.compare(p, passwd)

  def save(self, user, passwd):
    self.__db[user] = utils.passwd_tool.passwd(passwd)
    self.__db.sync()


class AuthSession(object):
  def __init__(self, auth_daemon, conn, max_tries, timeout):
    self.__auth_daemon = auth_daemon
    self.__conn = conn
    self.__tries = max_tries
    self.__timeout = timeout
    self.__state = LoginPrompt(self, conn)
    self.__timer = Timed_Event.from_delay(self, timeout)

    conn.connect_signals(self)

  @property
  def passwddb(self):
    return self.__auth_daemon.passwddb

  @proptery
  def tries(self):
    return self.__tries

  def decrement_tries(self):
    self.__tries -= 1

  def handle_disconnect(self, conn):
    if self.__timer:
      self.__timer.cancel()

    # this should decrement ref count and delete the AuthSession:
    self.__auth_daemon.done_auth(conn)

  def handle_interrupt(self):
    self.__timer += self.__timeout
    self.__state = LoginPrompt(self, self.__conn)

  def handle_line(self, line):
    self.__timer += self.__timeout
    newstate = None

    try:
      newstate = self.__state.handle_line(line)
    except StopIteration: 
      pass

    if newstate is None:
      self.__auth_daemon.done_auth(conn)
    else:
      self.__state = newstate

  def handle_timeout(self, now):
    self.__conn.push('Timeout....\n')
    self.__conn.close_when_done()
    self.__auth_daemon.done_auth(self.__conn)


class AuthDaemon(object):
  def __init__(self, passwd_db, max_tries=3, timeout=30):
    self.__passwd_db = passwd_db
    self.__tries = max_tries
    self.__timeout = timeout
    self.__auths = dict()
    signals.connection_signal.connect(self.auth)

  @property
  def passwddb(self):
    return self.__passwd_db

  def auth(self, conn):
    self.__auths[conn] = AuthSession(self, conn, self.__tries, self.__timeout)

  def done_auth(self, conn):
    auth = self.__auths.pop(conn, None)

