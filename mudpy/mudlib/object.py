import types
import weakref


class weaklist(list):
  def __init__(self, callback):
    self.__callback = callback

  def append(self, obj):
    if not isinstance(obj, weakref.ref):
      obj = obj.weakref(self.__callback)
    else:
      obj = obj().weakref(self.__callback)
    return super(weaklist, self).append(obj)

  def extend(self, other_list):
    for item in other_list:
      self.append(item)

  def insert(self, index, obj):
    if not isinstance(obj, weakref.ref):
      obj = obj.weakref(self.__callback)
    else:
      obj = obj().weakref(self.__callback)
    return super(weaklist, self).insert(obj)


class Object(object):
  def __init__(self, oid):
    super(Object, self).__init__()
    self.__oid = oid
    self.__inventory = weaklist(self.__de_ref)
    self.__environment = None

  def __de_ref(self, obj):
    cnt = self.__inventory.count(obj)
    for i in xrange(0, cnt):
      self.__inventory.remove(obj)
    if self.__environment == obj:
      self.__environment = None

  def __environment_set(self, objweakref):
    if not isinstance(objweakref, weakref.ref):
      raise TypeError(str(self) +
          " tried to set environment to non-weakref")
    self.__environment = objweakref

  environment = property(lambda self: self.__environment,
                         __environment_set)

  def __oid_set(self, newoid):
    self.__oid = newoid

  oid = property(lambda self: self.__oid,
                 __oid_set)

  @property
  def inventory(self):
    return self.__inventory    

  @property
  def props(self):
    raise NotImplementedError

  def reset(self):
    pass

  def restore(self, propdict):
    raise NotImplementedError

  def save(self):
    raise NotImplementedError

  def setup(self):
    pass

  def weakref(self, callback=None):
    return weakref.ref(self, callback)

  