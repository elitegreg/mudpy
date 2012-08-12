from mudpy.database import *

import types
import weakref


class TmpVars():
    pass

class weakset(set):
  def __init__(self, callback):
    self.__callback = callback

  def add(self, obj):
    if not isinstance(obj, weakref.ref):
      obj = obj.weakref(self.__callback)
    else:
      obj = obj().weakref(self.__callback)
    return super().add(obj)

  def discard(self, obj):
    if not isinstance(obj, weakref.ref):
      obj = obj.weakref(self.__callback)
    else:
      obj = obj().weakref(self.__callback)
    return super().discard(obj)

  def update(self, other_list):
    if isinstance(other_list, weakset):
      super().extend(other_list)
    else:
      for item in other_list:
        self.add(item)

  #TODO auto deref weakrefs on access


class Object():
  def __init__(self, oid):
    raise RuntimeError('Mudlib objects cannot be constructed!')

  def __de_ref(self, obj):
    self.inventory.discard(obj)
    if self.environment == obj:
      self.environment = None # TODO we need better logic here!

  def __getstate__(self):
    d = self.__dict__.copy()
    d.pop('_Object__oid')
    d.pop('_Object__inventory')
    d.pop('_Object__tmp')

    if self.environment:
      d['_Object__environment'] = self.environment.oid
    return d

  def __setstate__(self, newstate):
    self.__dict__ = newstate
    self.__inventory = weakset(self.__de_ref)
    self.__tmp = TmpVars()

    if hasattr(self, '_Object__environment'):
      oid = self.__environment
      self.environment = None
      move_object_to_oid(self, oid)
    else:
      self.__environment = None

  @property
  def environment(self):
    return self.__environment() if self.__environment else None

  @environment.setter
  def environment(self, newenv):
    if newenv is None or isinstance(newenv, weakref.ref):
      self.__environment = newenv
    else:
      self.__environment = newenv.weakref(self.__de_ref)

  @property
  def oid(self):
    return self.__oid

  @oid.setter
  def oid(self, value):
    assert(isinstance(value, Object_ID))
    self.__oid = value

  @property
  def inventory(self):
    return self.__inventory    

  @property
  def tmp(self):
    return self.__tmp    

  def save(self):
      DB().save_obj(self)

  def weakref(self, callback=None):
    return weakref.ref(self, callback)

  
def move_object(obj, newenv):
  oldenv = obj.environment
  if oldenv:
    oldenv.inventory.discard(obj)
    try:
      oldenv.notify_object_exit(obj)
    except AttributeError:
      pass

  obj.environment = newenv
  newenv.inventory.add(obj)


def move_object_to_oid(obj, oid):
  return move_object(obj, ObjectCache().get(oid))

