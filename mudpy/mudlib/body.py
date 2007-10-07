import Abilities
import Feats
import Skills
import Species


class Body(object):
  def __init__(self):
    self.__permanents = dict()
    self.__construct_new_body()

  def __getstate__(self):
    """
    This method is called when saving this object.

    @rtype  : dict
    @return : dictionary state to save
    """

    pass

  def __setstate__(self, state):
    """
    This method is called when restoring the state of a saved object.

    @type  state: dict
    @param state: dictionary state to restore
    """

    pass

  def __construct_new_body(self):
    """
    This method is intended to be called when creating a new body object
    as opposed to restoring an existing one.
    """

    pass
