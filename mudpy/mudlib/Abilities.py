import utils.rpg_utils

ABILITIES = [
    'Strength',
    'Dexterity',
    'Intelligence',
    'Wisdom',
    'Constitution',
    'Charisma',
]


def generate_abilities(is_hero=False):
  result = dict()
  for ability in ABILITIES:
    if is_hero:
      result[ability] = utils.rpg_utils.roll_dice(4, keep=3)
    else:
      result[ability] = utils.rpg_utils.roll_dice(3)
  return result

