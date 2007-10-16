import body

class Player(body.Body):
  def __init__(self):
    super(Player, self).__init__()
    self.__permanents = dict()
    self.__initialize_player()

  def getstate(self):
    """
    This method is called when saving this object.

    @rtype  : dict
    @return : dictionary state to save
    """

    d = super(Player, self).getstate()
    # save data here
    return d

  def setstate(self, state):
    """
    This method is called when restoring the state of a saved object.

    @type  state: dict
    @param state: dictionary state to restore
    """

    super(Player, self).setstate(state)
    self.__initialize_player()

  def __initialize_player(self):
    """
    This method is intended to be called when creating a new player object
    either by init or setstate
    """

    pass

