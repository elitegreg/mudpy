import bsddb
import os.path
import re
import shelve
import types
import utils.borg


##
## Object ID Format
## ================
##
## <DB>:<Obj Type>:/path/id[#<int: clone number>]
##
## DB: Db File to load/restore
## Obj type: string type id from obj.type (must be registered with ...)
## Path/Id: String id of object. Meaning of path depends on type.
## Clone Number: (optional) If object is a clone, an clone id number
##
## A cloneable object is an object that can only be copied (hence
## readonly from the DB). Only the DB can load the base object.
##
## E.g.:
##
## Player:
##   players.db:player:/players/greg
##
## Room:
##   rooms.db:room:
## 
## Weapons:
##   # Clone of a broadsword base
##   objects.db:sword:/broadsword#12345
##
##   # Clone of a pistol
##   objects.db:gun:/9mm_pistol#9876
##

# RegEx breaks into db, type, id, clone, clone_id
OBJECT_ID_FORMAT = re.compile(r"^(?P<db>[\w.]+):(?P<type>[\w.]+):" \
    "(?P<id>[\w./]+)((?P<clone>#)(?P<clone_id>\d+)?)?$")

class Object_ID(object):
  def __init__(self, id):
    if not type(id) == types.StringType:
      raise RuntimeError("Object_ID() invalid id: " + id)
    mo = OBJECT_ID_FORMAT.match(id)
    if not mo:
      raise RuntimeError("Object_ID() invalid id: " + id)
    self.__id = mo.group(0)
    self.__id_split = mo.groupdict()

  @property
  def db(self):
    return self.__id_split.get('db')

  @property
  def type(self):
    return self.__id_split.get('type')

  @property
  def id(self):
    id = self.__id_split.get('id')
    if self.is_clone:
      id += "#"
    return id

  @property
  def is_clone(self):
    if self.__id_split.get('clone'):
      return True
    return False

  @property
  def clone_id(self):
    return self.__id_split.get('clone_id')

  def __str__(self):
    return self.__id


class ObjectCache(utils.borg.Borg):
  __id_to_obj = dict()

  def __init__(self):
    super(ObjectCache, self).__init__()

  def get_obj(self, id, load=True, create=False):
    obj = self.__id_to_obj.get(id)
    if not obj:
      oid = Object_ID(id)
      if load and (oid.is_clone or oid.clone_id is None):
        obj = DB().load_obj(id, create)
        self.__id_to_obj[obj.id] = obj
      else:
        raise KeyError("ObjectCache: Object %s doesn't exist" % id)
    return obj

  def destroy(self, id_or_obj):
    if type(id_or_obj) in types.StringTypes:
      id = id_or_obj
      obj = self.__id_to_obj.get(id)
    else:
      id = id_or_obj.id
      obj = id_or_obj

    if obj:
      try:
        obj.destroy()
      except AttributeError:
        pass
      self.__id_to_obj.pop(id)


class DB(utils.borg.Borg):
  DBDIR = None

  __dbmap = dict()
  __typemap = dict()

  def __init__(self):
    super(DB, self).__init__()

  def __load_db(self, dbfile):
    if self.DBDIR:
      dbfile = os.path.join(self.DBDIR, dbfile)
    btree = bsddb.btopen(dbfile)
    return shelve.BsdDbShelf(btree, protocol=2)

  def __get_db(self, dbname):
    db = self.__dbmap.get(dbname)
    if not db:
      db = self.__load_db(dbname)
      self.__dbmap[dbname] = db
    return db

  def delete_id(self, id):
    oid = Object_ID(id)
    dbname = oid.db
    id = oid.id
    db = self.__get_db(obj.dbname)
    try:
      db.pop(id)
    except KeyError:
      pass
    db.sync()

  def load_obj(self, id, create_if_needed=False):
    pass

  def save_obj(self, obj):
    data = obj.save()
    data['object.type'] = obj.type
    db = self.__get_db(obj.dbname)
    id = Object_ID(obj.id).id
    db[id] = data
    db.sync()

  def register_type(self, type, class_type):
    if not callable(class_type):
      raise TypeError("DB failed to register type %s, not callable" % \
          type)
    self.__typemap[type] = class_type

