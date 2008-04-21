import inspect


def load_class(fullpath):
  if '.' in fullpath:
    (module, classname) = fullpath.rsplit('.', 1)
    module_obj = __import__(module, fromlist=classname)
  else:
    classname = fullpath
    module_obj = __main__

  class_obj = getattr(module_obj, classname)

  if inspect.isclass(class_obj):
    return class_obj

  raise RuntimeError(fullpath + ' is not a class')

