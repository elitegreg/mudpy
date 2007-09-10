from ConfigParser import SafeConfigParser

class Skills(object):
  def __init__(self):
    self.__all_skills = list()

  def load(self, config_file):
    parser = SafeConfigParser()
    parser.read(config_file)
    skill_names = parser.get('Skills', 'supported').split(',')
    for skill in skill_names:
      mod = __import__('skills.%s' % skill)
      skill_module = getattr(mod, skill, None)
      if skill_module is None:
        raise NotImpelementedError('No skill module: %s' % skill)
      skill_class = getattr(skill_module, skill, None)
      if skill_class is None:
        raise NotImpelementedError('No skill class: %s' % skill)
      self.__all_skills.append(skill_class())

  @property
  def all_skills(self):
    return self.__all_skills

