"""
Provide RPG (Role-Playing Game) Utility Funcions
"""

import random
import re


DICE_RE = re.compile('^(?P<count>\d+)[Dd](?P<sides>\d+)?$')
DIGITS_RE = re.compile('^\d+$')


def roll_dice(count, sides=6, keep=None, random_fun=random.randint):
  """
  Simulates dice rolls.

  @type  count: int > 0
  @param count: Number of dice to roll
  @type  sides: int > 0
  @param sides: Number of sides on each die (default: 6)
  @type  keep : int > 0
  @param keep : Number of count dice to keep. Throws out lowest rolls.
                (default: None, keep all)

  @rtype:  int
  @return: total rolled
  """

  rolls = list()
  for i in range(0, count):
    rolls.append(random_fun(1, sides))
  if keep is not None:
    if keep < count:
      rolls.sort()
      diff = count - keep
      rolls = rolls[diff:]

  return sum(rolls)


class Stat(object):
  __slots__ = ['__dice_map', '__constant']

  def __init__(self, dice_map, constant=0):
    self.__dice_map = dice_map
    self.__constant = constant

  def roll(self, modifier=0, minimum=None):
    dice_total = 0
    for (sides, count) in self.__dice_map.items():
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
      raise RuntimeError('Invalid dice string: %s' % dice_string)
    if DIGITS_RE.match(token):
      constant += int(token)
    else:
      mo = DICE_RE.match(token)
      if mo is None:
        raise RuntimeError('Invalid dice string: %s' % dice_string)

      count, sides = mo.groups()

      if sides is None:
        sides = 6

      count = int(count)
      sides = int(sides)

      if sides in dice_map:
        dice_map[sides] += count
      else:
        dice_map[sides] = count

  return (dice_map, constant)

