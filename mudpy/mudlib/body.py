import Abilities
import Feats
import Skills
import Species


class Body(object):
  def __init__(self):
    self.__permanents = dict()
    self.__initialize_body()

  def getstate(self):
    """
    This method is called when saving this object.

    @rtype  : dict
    @return : dictionary state to save
    """

    pass

  def setstate(self, state):
    """
    This method is called when restoring the state of a saved object.

    @type  state: dict
    @param state: dictionary state to restore
    """

    self.__initialize_body()

  def __initialize_body(self):
    """
    This method is intended to be called when creating a new body object
    either by init or setstate
    """

    pass

