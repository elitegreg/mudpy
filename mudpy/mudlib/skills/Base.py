class SkillBase(object):
  @property
  def name(self):
    raise NotImplementedError

  @property
  def ability(self):
    raise NotImplementedError

  @property
  def armor_check_penalty(self):
    return False

  @property
  def trained_only(self):
    return False

  @property
  def retry(self):
    return True

  @property
  def commands(self):
    return []

