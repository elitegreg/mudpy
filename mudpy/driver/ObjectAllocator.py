import sys
import types


class InvalidModuleError(RuntimeError):
  pass


class ObjectAllocator(object):
  def __init__(self, config):
    self.__runtime_id = 0
    self.__id_obj_map = dict()
    self.__modules = dict()
    
    corelib_path = config.get('Path', 'Corelib', 'corelib')
    mudlib_path = config.get('Path', 'Mudlib', '../lib')
    sys.path.append(mudlib_path)
    sys.path.append(corelib_path)

  def load_module(self, module_string):
    module = self.__modules.get(module_string)
    if module is None:
      try:
        module = __import__(module_string)
      except Exception, e:
        raise InvalidModuleError(e)
    return module

  def unload_module(self, module):
    return self.__modules.pop(module, None)

  def clone_object(self, object_type):
    try:
      module = self.load_module(object_type)

      if object_type.find('.') >= 0:
        for part in object_type.split('.')[1:]:
          module = getattr(module, part) 

      module_member = object_type.rsplit('.', 1)[-1]
      obj_class = getattr(module, module_member)
      obj = obj_class(self, self.__runtime_id)
      obj.setup()
      self.__id_obj_map[self.__runtime_id] = obj
      self.__runtime_id += 1
      return obj
    except Exception, e:
      raise
      self.unload_module(object_type)
      raise InvalidModuleError(e)

  def remove_object(self, object_id):
    return self.__id_obj_map.pop(object_id, None)

