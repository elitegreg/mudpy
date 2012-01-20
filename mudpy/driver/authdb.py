import shelve

from mudpy.utils import passwd_tool
from mudpy.utils.borg import Borg

class AuthDB(Borg):
  def __contains__(self, key):
    return key in self.__db

  def load(self, pathname):
    self.__db = shelf.open(pathname)

  def setpassword(self, key, passwd):
    self.__db[key] = passwd
    self.__db.sync()

  def check(self, key, passwd):
    passwd_tool.compare(self.__db[key], passwd)

