import bsddb
import class_loader
import copy
import os.path
import re
import shelve
import types
import utils.borg


##
## Object ID Format
## ================
##
## <DB>:/path/id[#<int: clone number>]
##
## DB: Db File to load/restore
## Obj type: string type id (must be registered with DB)
## Path/Id: String id of object. Meaning of path depends on type.
## Clone Number: (optional) If object is a clone, an clone id number
##
## A cloneable object is an object that can only be copied (hence
## readonly from the DB). Only the DB can load the base object.
##
## E.g.:
##
## Player:
##   players.db:/players/greg
##
## Room:
##   rooms.db:/some/room/path
## 
## Weapons:
##   # Clone of a broadsword base
##   objects.db:/broadsword#12345
##
##   # Clone of a pistol
##   objects.db:/9mm_pistol#9876
##

# RegEx breaks into db, type, id, clone, clone_id
OBJECT_ID_FORMAT = re.compile(r'^(?P<dbname>[\w.]+):' \
    '(?P<id>[\w./]+)((?P<clone>#)(?P<clone_id>\d+)?)?$')

class Object_ID(object):
  def __init__(self, id):
    id = str(id)
    mo = OBJECT_ID_FORMAT.match(id)
    if not mo:
      raise RuntimeError('Object_ID() invalid id: ' + id)
    self.__id = mo.group(0)
    self.__id_split = mo.groupdict()

  @property
  def dbname(self):
    return self.__id_split.get('dbname')

  @property
  def id(self):
    return self.__id_split.get('id')

  @property
  def is_clone(self):
    if self.__id_split.get('clone'):
      return True
    return False

  @property
  def clone_id(self):
    return self.__id_split.get('clone_id')

  @property
  def oid(self):
    return self.__id

  def add_clone_id(self, cid):
    if not self.is_clone:
      raise RuntimeError(
          'Object_ID: Trying to add clone id to non-clone')
    cid = str(cid)
    self.__id_split['clone_id'] = cid
    self.__id = '%s:%s#%s' % (self.dbname, self.id, cid)

  def drop_clone(self):
    self.__id_split.pop('clone')
    self.__id_split.pop('clone_id')
    self.__id = '%s:%s' % (self.dbname, self.id)

  def __str__(self):
    return self.oid


class ObjectCache(utils.borg.Borg):
  __global_clone_id = 1
  __id_to_obj = dict()

  def __init__(self):
    super(ObjectCache, self).__init__()

  def clear(self):
    'This should only be called when testing the object cache!'
    self.__id_to_obj.clear()

  def get_obj(self, oid, create=None):
    '''Loads an object with given oid. create can be the object
       class, if an object should be created if one doesn't exist. '''
    oid_obj = Object_ID(oid)
    obj = self.__id_to_obj.get(oid_obj.oid)
    if not obj:
      if oid_obj.is_clone:
        if oid_obj.clone_id:
          # has clone id, but object not in cache. Object has
          # been destroyed. Raise KeyError
          raise KeyError("ObjectCache: Object %s doesn't exist" % oid)
        else:
          if not create:
            raise KeyError(
                'ObjectCache: create flag not set for oid: %s' % oid)

          # request to clone an object
          base_obj_oid = Object_ID(oid)
          base_obj_oid.drop_clone()
          base_obj = self.get_obj(base_obj_oid.oid, create)
          oid_obj.add_clone_id(self.__global_clone_id)
          obj = copy.deepcopy(base_obj)
          obj.oid = oid_obj.oid
          obj.setup() # setup the newly created object
          self.__global_clone_id += 1
      else:
        obj = DB().load_obj(oid, create)

      # store the obj in the cache
      self.__id_to_obj[oid_obj.oid] = obj

    return obj

  def destroy(self, oid):
    obj = self.__id_to_obj.get(oid)

    if obj:
      try:
        obj.destroy()
      except AttributeError:
        pass
      self.__id_to_obj.pop(oid)


class DB(utils.borg.Borg):
  DBDIR = None

  __dbmap = dict()

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

  def delete_id(self, oid):
    oid_obj = Object_ID(oid)
    db = self.__get_db(oid_obj.dbname)
    try:
      db.pop(oid_obj.id)
    except KeyError:
      pass
    db.sync()

  def load_obj(self, oid, create_if_needed=None):
    '''Loads an object with given oid. create_if_needed can be the object
       class, if an object should be created if one doesn't exist. '''
    oid_obj = Object_ID(oid)
    db = self.__get_db(oid_obj.dbname)
    try:
      data = copy.deepcopy(db[oid_obj.id])
    except KeyError:
      if create_if_needed:
        obj_class = create_if_needed
      else:
        raise
    else:
      obj_class = class_loader.load_class(data['__obj_type__'])
      data.pop('__obj_type__')

    obj = obj_class(oid)
    if create_if_needed:
      obj.setup()
    else:
      obj.restore(data)
    return obj

  def save_obj(self, obj):
    obj_type = '%s.%s' % (obj.__class__.__module__, obj.__class__.__name__)

    data = obj.save()
    data['__obj_type__'] = obj_type

    oid_obj = Object_ID(obj.oid)
    if oid_obj.is_clone:
      raise RuntimeError("Cloned object can't be saved")

    db = self.__get_db(oid_obj.dbname)
    db[oid_obj.id] = data
    db.sync()

