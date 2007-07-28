import random
import re

DICE_RE = re.compile('^(?P<count>\d+)[Dd](?P<sides>\d+)?$')
DIGITS_RE = re.compile('^\d+$')

def roll_dice(count, sides=6):
  dice_total = 0
  for i in xrange(0, count):
    dice_total += random.randint(1, sides)
  return dice_total


class Stat(object):
  __slots__ = ['__dice_map', '__constant']

  def __init__(self, dice_map, constant=0):
    self.__dice_map = dice_map
    self.__constant = constant

  def roll(self, modifier=0, minimum=None):
    dice_total = 0
    for (sides, count) in self.__dice_map.iteritems():
      dice_total += roll_dice(count, sides)

    total = dice_total + self.__constant + modifier

    if minimum is not None:
      total = max(total, minimum) 

    return total

  @staticmethod
  def from_dice_string(dice_string):
    return Stat(*parse_dice_string(dice_string))


def parse_dice_string(dice_string):
  constant = 0
  dice_map = dict()

  for token in dice_string.split('+'):
    if len(token) == 0:
      raise RuntimeError, 'Invalid dice string: %s' % dice_string
    if DIGITS_RE.match(token):
      constant += int(token)
    else:
      mo = DICE_RE.match(token)
      if mo is None:
        raise RuntimeError, 'Invalid dice string: %s' % dice_string

      count, sides = mo.groups()

      if sides is None:
        sides = 6

      count = int(count)
      sides = int(sides)

      if dice_map.has_key(sides):
        dice_map[sides] += count
      else:
        dice_map[sides] = count

  return (dice_map, constant)

