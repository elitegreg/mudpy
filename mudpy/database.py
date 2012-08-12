import copy
import os
import os.path
import re
import yaml

from . import config
from . import logging

from mudpy.utils.borg import Borg
from mudpy.utils.filesystem import mkdir


class DoesNotExist(RuntimeError):
  pass


##
## Object ID Format
## ================
##
## /path/id[#<int: clone number>]
##
## Path/Id: Unique path to object in DB
## Clone Number: (optional) If object is a clone, a clone id number
##

# RegEx breaks into db, type, id, clone, clone_id
OBJECT_ID_FORMAT = re.compile(r'^(?P<path>[\w./]+)((?P<clone>#)(?P<clone_id>\d+)?)?$')


class Object_ID(yaml.YAMLObject):
  yaml_loader = yaml.SafeLoader
  yaml_tag = '!ID'

  @classmethod
  def from_yaml(cls, loader, node):
    return Object_ID(loader.construct_scalar(node))

  @classmethod
  def to_yaml(cls, dumper, data):
    return dumper.represent_scalar('!ID', repr(data))

  def __init__(self, oid):
    super().__init__()
    oid = str(oid)
    mo = OBJECT_ID_FORMAT.match(oid)
    if not mo:
      raise RuntimeError('Object_ID() invalid id: ' + oid)
    self.__oid = mo.group(0)
    self.__oid_split = mo.groupdict()

  @property
  def path(self):
    return self.__oid_split.get('path')

  @property
  def is_clone(self):
    if self.__oid_split.get('clone'):
      return True
    return False

  @property
  def clone_id(self):
    return self.__oid_split.get('clone_id')

  @property
  def oid(self):
    return self.__oid

  def add_clone_id(self, cid):
    if not self.is_clone:
      raise RuntimeError(
          'Object_ID: Trying to add clone id to non-clone')
    cid = str(cid)
    newid = copy.deepcopy(self)
    newid.__oid_split['clone_id'] = cid
    newid.__oid = '%s#%s' % (self.oid, cid)
    return newid

  def drop_clone(self):
    newid = copy.deepcopy(self)
    newid.__oid_split.pop('clone')
    newid.__oid_split.pop('clone_id')
    newid.__oid = newid.oid
    return newid

  def __repr__(self):
    return self.oid


class ObjectCache(Borg):
  __global_clone_id = 0
  __id_to_obj = dict()

  def clear(self):
    'This should only be called when testing the object cache!'
    self.__id_to_obj.clear()

  def get(self, oid, create=None, createdict=None):
    '''Loads an object with given oid. create can be the object
       class, if an object should be created if one doesn't exist. '''
    assert(isinstance(oid, Object_ID))

    obj = self.__id_to_obj.get(oid)

    if not obj:
      if oid.is_clone:
        if oid.clone_id:
          # has clone id, but object not in cache. Object has
          # been destroyed. Raise KeyError
          raise KeyError("ObjectCache: Object %s doesn't exist" % oid)
        else:
          if not create:
            raise KeyError(
                'ObjectCache: create flag not set for oid: %s' % oid)

          # request to clone an object
          base_obj_oid = oid.drop_clone()
          base_obj = self.get(base_obj_oid, create)
          self.__global_clone_id += 1
          oid = oid.add_clone_id(self.__global_clone_id)
          obj = copy.deepcopy(base_obj)
          obj.oid = oid
      else:
        obj = DB().load(oid, create, createdict)

      # store the obj in the cache
      self.__id_to_obj[oid] = obj

    return obj

  def destroy(self, oid):
    obj = self.__id_to_obj.get(oid)

    if obj:
      try:
        obj.destroy()
      except AttributeError:
        pass
      self.__id_to_obj.pop(oid)


class DB(Borg):
  def __fix_path(self, oid):
    path = repr(oid)
    if os.sep != '/':
      path = path.replace('/', os.sep)
    path = os.path.join(config.db.path, path[1:])
    return path

  def delete_id(self, oid):
    if oid.is_clone:
      raise RuntimeError("DB: Cannot delete clone object: %s" % oid)
    os.unlink(self.__fix_path(oid))

  def load(self, oid, create=None, createdict=None):
    '''Loads an object with given oid. create_if_needed can be the object
       class, if an object should be created if one doesn't exist. '''

    try:
      path = self.__fix_path(oid)
      logging.debug('DB:load(oid={})', oid, path)
      with open(path) as fd:
        obj = yaml.safe_load(fd)
      obj.oid = oid
      return obj
    except IOError:
      if create:
        if not createdict:
          createdict = dict()
        createdict['_Object__oid'] = oid
        obj = create.__new__(create)
        obj.__setstate__(createdict)
        return obj
      raise DoesNotExist

  def save_obj(self, obj):
    oid = obj.oid
    if oid.is_clone:
      raise RuntimeError("Cloned object can't be saved: %s" % oid)
    path = self.__fix_path(oid)
    logging.debug('DB:save_obj(oid={}): path={}', oid, path)
    dirname = os.path.dirname(path)
    mkdir(dirname)
    with open(path, 'w') as fd:
      yaml.dump(obj, fd, explicit_start=True, width=72, indent=4, default_flow_style=False)

