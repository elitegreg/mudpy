class Borg(object):
  """
    This is an implementation of the Borg (shared-state) idiom.
    To use, just inherit from this class (must be new-style).
  """

  _state = {}

  def __init__(self):
    super(Borg, self).__init__()

  def __new__(cls, *p, **k):
    self = object.__new__(cls, *p, **k)
    self.__dict__ = cls._state
    return self
