import utils.rpg_utils
import unittest


class Rpg_utils_TestCase(unittest.TestCase):
  def test_roll_min_max(self):
    '''Tests that for a given set of dice, the min and max is seen over
    1000 rolls'''

    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(utils.rpg_utils.roll_dice(1))
    self.assertEquals(min(*rolls), 1)
    self.assertEquals(max(*rolls), 6)

    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(utils.rpg_utils.roll_dice(1, 20))
    self.assertEquals(min(*rolls), 1)
    self.assertEquals(max(*rolls), 20)

    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(utils.rpg_utils.roll_dice(2))
    self.assertEquals(min(*rolls), 2)
    self.assertEquals(max(*rolls), 12)

  def test_dice_string_parsing(self):
    '''Tests dice string parsing'''
    (dice, constant) = utils.rpg_utils.parse_dice_string('2D+2')
    self.assertEquals(constant, 2)
    self.assertEquals(dice, {6:2})

    (dice, constant) = \
      utils.rpg_utils.parse_dice_string('1d20+3d4+2d4+1d20+1')
    self.assertEquals(constant, 1)
    self.assertEquals(dice, {20: 2, 4: 5})

    (dice, constant) = \
      utils.rpg_utils.parse_dice_string('15')
    self.assertEquals(constant, 15)
    self.assertEquals(dice, {})

    self.assertRaises(RuntimeError, utils.rpg_utils.parse_dice_string,
        '+1d2+1')
    self.assertRaises(RuntimeError, utils.rpg_utils.parse_dice_string,
        '1d2+1+')
    self.assertRaises(RuntimeError, utils.rpg_utils.parse_dice_string,
        '1d-1')
    self.assertRaises(RuntimeError, utils.rpg_utils.parse_dice_string,
        'd20+1')

  def test_Stat_rolls_min_max(self):
    '''Tests that Stat()s can be created and roll the correct min/max'''
    s = utils.rpg_utils.Stat({5: 2}, 2)
    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(s.roll())
    self.assertEquals(min(*rolls), 4)
    self.assertEquals(max(*rolls), 12)

    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(s.roll(modifier=-10, minimum=0))
    self.assertEquals(min(*rolls), 0)
    self.assertEquals(max(*rolls), 2)

    s = utils.rpg_utils.Stat.from_dice_string('2d+1')
    rolls = list()
    for i in xrange(0, 1000):
      rolls.append(s.roll())
    self.assertEquals(min(*rolls), 3)
    self.assertEquals(max(*rolls), 13)


if __name__ == '__main__':
  unittest.main()

