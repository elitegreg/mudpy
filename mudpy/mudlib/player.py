import body
import utils.ansi
import utils.passwd_tool

from sqlalchemy import Column, Integer, Text, Table
from sqlalchemy.orm import mapper


class Player(body.Body):
  # Database fields
  name     = None
  password = None
  email    = None
  gender   = None
  species  = None
  age      = None

  def __init__(self, name, password, email, gender, species, age):
    super(Player, self).__init__()
    self.name     = name
    self.password = utils.passwd_tool.passwd(password)
    self.email    = email
    self.gender   = gender
    self.species  = species
    self.age      = age
    self.__conn   = None
    self.__ansi_map = utils.ansi.DEFAULT_MAP

  def handle_disconnect(self):
    pass

  def handle_interrupt(self):
    pass

  def handle_line(self, line):
    pass

  def handle_telnet_connected(self, conn):
    self.__conn = conn
    if utils.ansi.is_color_term(conn.termtype):
      self.__ansi_map = utils.ansi.ANSI_MAP

  def reset(self):
    super(Player, self).reset()

  def setup(self):
    super(Player, self).setup()

  def write(self, buffer):
    self.__conn.write(buffer)


def register_table(metadata):
  players_table = Table('players', metadata,
      Column('id', Integer, primary_key=True),
      Column('name', Text, index=True),
      Column('password', Text),
      Column('email', Text),
      Column('gender', Text),
      Column('species', Text),
      Column('age', Integer))

  mapper(Player, players_table)


def check_login(db_session, user, password):
  for row in db_session.query(Player.password).filter(
      Player.name == user.lower()):
    return utils.passwd_tool.compare(row.password, password)
  return None


def is_unused_name(db_session, user):
  for row in db_session.query(Player.name).filter(
      Player.name == user.lower()):
    return False
  return True


