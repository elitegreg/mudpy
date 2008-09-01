import database
import mudlib.player
import signals

from NewUserQuestionaire import NewUserQuestionaire
from NewUserQuestionaire import QuestionError


class AuthComplete(Exception):
  pass


class LoginPrompt(object):
  def __init__(self, auth_session, conn):
    self.__auth_session = auth_session
    self.__conn = conn

    if auth_session.tries <= 0:
      conn.push('Too many tries.... closing....\n')
      conn.close_when_done()
      raise AuthComplete

    conn.push("Username (or 'new'): ")

  def handle_line(self, username):
    self.__auth_session.decrement_tries()

    username = username.lower()

    if username != 'new':
      return PasswordPrompt(self.__auth_session, self.__conn,
          name=username)
    else:
      return NewUserPrompt(self.__auth_session, self.__conn)


class PasswordPrompt(object):
  def __init__(self, auth_session, conn, **kwargs):
    self.__auth_session = auth_session
    self.__conn = conn
    self.__state = kwargs
    conn.disable_local_echo()
    conn.push('Password: ')

  def handle_line(self, password):
    self.__conn.enable_local_echo()
    self.__conn.push('\n')
    if mudlib.player.check_login(database.Session(),
        self.__state['name'], password):
      self.__conn.push('Login Successful.\n\n')
      signals.user_authorized_signal(self.__conn, self.__state['name'])
      return None
    else:
      self.__conn.push('Incorrect password....\n')
      signals.user_unauthorized_signal(self.__conn, self.__state['name'])
      return LoginPrompt(self.__auth_session, self.__conn)


class NewUserPrompt(object):
  def __init__(self, auth_session, conn):
    self.__auth_session = auth_session
    self.__conn = conn
    self.__state = dict()
    self.__questionaire = NewUserQuestionaire('etc/new_user.cfg')
    self.__question_num = 0
    self.__question = self.__questionaire.questions[self.__question_num]

    self.__conn.push(self.__questionaire.messages['initial'])

    self.__question.prompt(self.__conn)

  def handle_line(self, response):
    try:
      self.__question.respond(response, self.__state)
      self.__question_num += 1
    except QuestionError, e:
      self.__conn.push(str(e))

    if self.__question_num >= len(self.__questionaire.questions):
      cap_name = self.__state['name'].capitalize()
      props = self.__state.copy()
      props['name'] = props['name'].capitalize()
      self.__conn.push(self.__questionaire.messages['final'] % props)
      signals.new_user_signal(self.__conn, self.__state)
      return None
    else:
      self.__question = self.__questionaire.questions[self.__question_num]

    self.__question.prompt(self.__conn)

    return self

