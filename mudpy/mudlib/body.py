import Abilities
import Feats
import object
import Skills
import Species


class Body(object.Object):
  def __init__(self):
    self.__permanents = dict()

  @property
  def props(self):
    return self.__permanents

  def save(self):
    raise NotImplementedError

  def reset(self):
    super(Body, self).reset()

  def restore(self, propdict):
    raise NotImplementedError

  def setup(self):
    super(Body, self).setup()

