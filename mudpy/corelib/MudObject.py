import MudLibException

class MudObject(object):
  def __init__(self, db, heartbeat_daemon):
    self.__db = db
    self.__hb_daemon = heartbeat_daemon
    self.__environment = None
    self.__inventory = list()
    self.__properties = dict()

  db          = property(lambda self: self.__db)
  environment = property(lambda self: self.__environment)
  inventory   = property(lambda self: self.__inventory)
  properties  = property(lambda self: self.__properties)

  def move(self, dest):
    if dest and hasattr(dest, 'inventory'):
      if self.__environment is not None:
        self.__environment.inventory.remove(self)
      self.__environment = dest
      self.__environment.inventory.append(self)
    else:
      raise MudLibException("move() destination invalid")

  def receive_message(self, msg_class, msg):
    pass

  def reset(self):
    pass

  def set_heartbeat(self, flag):
    slot = getattr(self, 'heartbeat', None)
    if flag:
      if not slot:
        raise MudLibException("Object doesn't have a heartbeat function!")
      self.__hb_daemon.heartbeat_signal.connect(slot)
    else:
      self.__hb_daemon.heartbeat_signal.connect(slot)

  def setup(self):
    pass

