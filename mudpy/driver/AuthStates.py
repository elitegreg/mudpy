import signals


class LoginPrompt(object):
  def __init__(self, auth_session, conn):
    self.__auth_session = auth_session
    self.__conn = conn

    if auth_session.tries <= 0:
      conn.push('Too many tries.... closing....\n')
      conn.close_when_done()
      raise StopIteration

    conn.push("Username (or 'new'): ")

  def handle_line(self, username):
    self.__auth_session.decrement_tries()

    username = username.lower()

    if username != 'new':
      if username not in self.__auth_session.passwddb:
        conn.push('User does not exist....\n')
        return LoginPrompt(self.__auth_session, self.__conn)
      return PasswordPrompt(self.__auth_session, self.__conn,
          user=username)
    else:
      return NewUserPrompt(self.__auth_session, self.__conn)


class PasswordPrompt(object):
  def __init__(self, auth_session, conn, **kwargs):
    self.__auth_session = auth_session
    self.__conn = conn
    conn.disable_local_echo()
    conn.push('Password: ')

  def handle_line(self, password):
    self.__conn.enable_local_echo()
    if self.__auth_session.passwddb.compare(kwargs['user'], password):
      conn.push('Login Successful.\n\n')
      signals.user_authorized_signal(self.__conn, kwargs['user'])
      return None
    else
      conn.push('Incorrect password....\n')
      signals.user_unauthorized_signal(self.__conn, kwargs['user'])
      return LoginPrompt(self.__auth_session, conn)


class NewUserPrompt(object):
  def __init__(self, auth_session, conn):
    self.__auth_session = auth_session
    self.__conn = conn
    raise NotImplementedError

