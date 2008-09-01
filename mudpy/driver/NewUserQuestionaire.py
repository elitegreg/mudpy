import database
import mudlib.player
import re

from ConfigParser import SafeConfigParser


class QuestionError(RuntimeError):
  def __init__(self, msg):
    super(QuestionError, self).__init__(msg)


class Question(object):
  def __init__(self, question_msg):
    super(Question, self).__init__()
    self.__question_msg = question_msg
    self.__type = None
    self.__field = None
    self.__choices = None
    self.__check = None
    self.__check_fail_msg = None
    self.__no_echo = False

  def load(self, config, section, prefix):
    self.__type = config.get(section, '%s_type' % prefix).lower()
    self.__field = config.get(section, '%s_field' % prefix).lower()

    if self.__type == 'choice':
      self.__choices = config.get(section, '%s_choices' % \
          prefix).lower().split(',')
    
    if config.has_option(section, '%s_check' % prefix):
      self.__check = config.get(section, '%s_check' % prefix)
    else:
      self.__check = None

    if config.has_option(section, '%s_check_fail_msg' % prefix):
      self.__check_fail_msg = \
          config.get(section, '%s_check_fail_msg' % prefix)
    else:
      self.__check_fail_msg = 'Invalid value'

    if config.has_option(section, '%s_no_echo' % prefix):
      self.__no_echo = \
          config.get(section, '%s_no_echo' % prefix).lower() == 'true'
    else:
      self.__no_echo = False


  def prompt(self, conn):
    if self.__choices:
      msg = '%s (%s) ' % (self.__question_msg, ','.join(self.__choices))
    else:
      msg = self.__question_msg + ' '

    conn.wrapwrite(msg)

    if self.__no_echo:
      conn.disable_local_echo()

  def respond(self, conn, response, value_dict=None):
    if self.__no_echo:
      conn.wrapwrite('', newlines=1)
      conn.enable_local_echo()

    response = response.lower()

    if self.__type == 'int':
      try:
        answer = int(response)
      except ValueError:
        raise QuestionError('Must be an integer')
    elif self.__type == 'float':
      try:
        answer = float(response)
      except ValueError:
        raise QuestionError('Must be numeric')
    elif self.__type == 'choice':
      if response not in self.__choices:
        raise QuestionError('Invalid choice')
      answer = response
    else:
      answer = response

    if self.__check:
      exec self.__check
      if not check_result:
        raise QuestionError(self.__check_fail_msg)

    if value_dict is not None:
      original = value_dict.get(self.__field)
      if original is not None:
        if answer != original:
          raise QuestionError('Does not match!')
      value_dict[self.__field] = answer


class NewUserQuestionaire(object):
  def __init__(self, config_file):
    parser = SafeConfigParser()
    parser.read(config_file)

    self.__questions = list()
    self.__messages  = dict()

    if not parser.has_section('Questions'):
      raise RuntimeError(
          'NewUserQuestionaire config: no Questions section')
    if not parser.has_section('Messages'):
      raise RuntimeError(
          'NewUserQuestionaire config: no Messages section')

    for question_number in xrange(1, 99):
      item = 'question%s' % question_number
      if not parser.has_option('Questions', item):
        break
      question = Question(parser.get('Questions', item))
      question.load(parser, 'Questions', item)
      self.__questions.append(question)

    self.__messages['initial'] = parser.get('Messages',
        'message_initial')
    self.__messages['final'] = parser.get('Messages',
        'message_final')

  @property
  def messages(self):
    return self.__messages

  @property
  def questions(self):
    return self.__questions

