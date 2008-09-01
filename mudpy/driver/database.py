import sqlalchemy
import sqlalchemy.orm
import utils.borg


class Database(utils.borg.Borg):
  def __init__(self):
    super(Database, self).__init__()

  def __getattr__(self, name):
    return getattr(self.__db, name)

  def open_db(self, url):
    self.__db = sqlalchemy.create_engine(url)


class Session(utils.borg.Borg):
  def __init__(self):
    super(Session, self).__init__()

  def __getattr__(self, name):
    return getattr(self.__session, name)

  def open_session(self, db):
    self.__session = sqlalchemy.orm.sessionmaker(bind=db,
        autoexpire=False, autoflush=False, autocommit=False)()


class ObjectCache(utils.borg.Borg):
  __session = Session()
  __table_id_obj = dict()

  def __init__(self):
    super(ObjectCache, self).__init__()

  def clear(self):
    'This should only be called when testing the object cache!'
    self.__table_id_obj.clear()

  def lookup(self, obj_class, id):
    '''Loads an object of type obj_class with the given id'''
    id_dict = self.__table_id_obj.setdefault(obj_class, dict())
    obj = id_dict.get(id)

    if obj is None:
      obj = self.__session.query(obj_class).get(id)
      if obj:
        self.__session.expunge(obj)
        id_dict[id] = obj
        obj.setup()

    return obj

  def save(self, obj):
    self.__session.add(obj)
    self.__session.commit()
    self.__session.expunge(obj)

