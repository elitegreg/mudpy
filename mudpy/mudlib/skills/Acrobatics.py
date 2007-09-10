import Base

class Acrobatics(Base.SkillBase):
  @property
  def name(self):
    return "Acrobatics"

  @property
  def ability(self):
    return "Dexterity"

  @property
  def armor_check_penalty(self):
    return True

  @property
  def commands(self):
    return []
