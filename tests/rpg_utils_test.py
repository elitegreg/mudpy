from mudpy.utils import rpg_utils

import random
import unittest


# Seed with a common seed so that we get predictable results
random.seed(0)


class Rpg_utils_TestCase(unittest.TestCase):
  def test_roll_min_max(self):
    '''Tests that for a given set of dice, the min and max is seen over
    1000 rolls'''

    rolls = list()
    for i in range(0, 20):
      rolls.append(rpg_utils.roll_dice(1))
    self.assertEqual(min(*rolls), 1)
    self.assertEqual(max(*rolls), 6)

    rolls = list()
    for i in range(0, 50):
      rolls.append(rpg_utils.roll_dice(1, 20))
    self.assertEqual(min(*rolls), 1)
    self.assertEqual(max(*rolls), 20)

    rolls = list()
    for i in range(0, 90):
      rolls.append(rpg_utils.roll_dice(2))
    self.assertEqual(min(*rolls), 2)
    self.assertEqual(max(*rolls), 12)

    rolls = list()
    for i in range(0, 1700):
      rolls.append(rpg_utils.roll_dice(4, keep=3))
    self.assertEqual(min(*rolls), 3)
    self.assertEqual(max(*rolls), 18)

  def test_dice_string_parsing(self):
    '''Tests dice string parsing'''
    (dice, constant) = rpg_utils.parse_dice_string('2D+2')
    self.assertEqual(constant, 2)
    self.assertEqual(dice, {6:2})

    (dice, constant) = \
      rpg_utils.parse_dice_string('1d20+3d4+2d4+1d20+1')
    self.assertEqual(constant, 1)
    self.assertEqual(dice, {20: 2, 4: 5})

    (dice, constant) = \
      rpg_utils.parse_dice_string('15')
    self.assertEqual(constant, 15)
    self.assertEqual(dice, {})

    self.assertRaises(RuntimeError, rpg_utils.parse_dice_string,
        '+1d2+1')
    self.assertRaises(RuntimeError, rpg_utils.parse_dice_string,
        '1d2+1+')
    self.assertRaises(RuntimeError, rpg_utils.parse_dice_string,
        '1d-1')
    self.assertRaises(RuntimeError, rpg_utils.parse_dice_string,
        'd20+1')

  def test_Stat_rolls_min_max(self):
    '''Tests that Stat()s can be created and roll the correct min/max'''
    s = rpg_utils.Stat({5: 2}, 2)
    rolls = list()
    for i in range(0, 40):
      rolls.append(s.roll())
    self.assertEqual(min(*rolls), 4)
    self.assertEqual(max(*rolls), 12)

    rolls = list()
    for i in range(0, 40):
      rolls.append(s.roll(modifier=-10, minimum=0))
    self.assertEqual(min(*rolls), 0)
    self.assertEqual(max(*rolls), 2)

    s = rpg_utils.Stat.from_dice_string('2d+1')
    rolls = list()
    for i in range(0, 50):
      rolls.append(s.roll())
    self.assertEqual(min(*rolls), 3)
    self.assertEqual(max(*rolls), 13)


if __name__ == '__main__':
  unittest.main()

