from MudLibException import *
from MudObject import *

from storm.locals import *


class PlayerProperties(object):
  __storm_table__ = 'player'
  id = Int(primary=True)
  name = Chars()
  password = Chars()
  last_login = DateTime()
  last_ip = Chars()


class Player(MudObject):
  player_properties = property(lambda self: self.__data)

  def load(self, username):
    data = self.db.find(PlayerProperties, PlayerProperties.name == username).one()
    if data:
      self.__data = data
      return True
    self.__data = PlayerProperties()

  def save(self):
    if len(self.__data.name) == 0:
      raise MudLibException, 'Player.save(): username not set'
    if len(self.__data.password) == 0:
      raise MudLibException, 'Player.save(): password not set'
    self.db.add(self.__data)
    self.db.flush()
    self.db.commit()

