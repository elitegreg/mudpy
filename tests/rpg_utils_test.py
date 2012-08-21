from mudpy.utils import rpg_utils

import unittest


def rand_min(minimum, maximum):
    return minimum


def rand_max(minimum, maximum):
    return maximum


class AlternateRandom:
    def __init__(self, minimum=False, maximum=False):
        if (not minimum and not maximum) or \
           (minimum and maximum):
            raise RuntimeError('AlternateRandom must be in min or max mode')
        if minimum:
            self.func = rand_min
        elif maximum:
            self.func = rand_max

    def __enter__(self):
        self.old_func = rpg_utils.randint
        rpg_utils.randint = self.func

    def __exit__(self, *args, **kwargs):
        rpg_utils.randint = self.old_func

# TODO this set of tests should not use random!

class Rpg_utils_TestCase(unittest.TestCase):
    def test_randint(self):
        'This test is just for code coverage completeness'
        self.assertTrue(type(rpg_utils.randint(0, 6)) is int)

    def test_roll_min(self):
        'Tests that for a given set of dice, the min is seen'

        # replace randint with out mock random function
        with AlternateRandom(minimum=True):
            self.assertEqual(rpg_utils.roll_dice(1), 1)
            self.assertEqual(rpg_utils.roll_dice(1, 20), 1)
            self.assertEqual(rpg_utils.roll_dice(2), 2)
            self.assertEqual(rpg_utils.roll_dice(4, keep=3), 3)

    def test_roll_max(self):
        'Tests that for a given set of dice, the max is seen'

        # replace randint with out mock random function
        with AlternateRandom(maximum=True):
            self.assertEqual(rpg_utils.roll_dice(1), 6)
            self.assertEqual(rpg_utils.roll_dice(1, 20), 20)
            self.assertEqual(rpg_utils.roll_dice(2), 12)
            self.assertEqual(rpg_utils.roll_dice(4, keep=3), 18)

    def test_dice_string_parsing(self):
        'Tests dice string parsing'
        (dice, constant) = rpg_utils.parse_dice_string('2D+2')
        self.assertEqual(constant, 2)
        self.assertEqual(dice, {6:2})
  
        (dice, constant) = rpg_utils.parse_dice_string('1d20+3d4+2d4+1d20+1')
        self.assertEqual(constant, 1)
        self.assertEqual(dice, {20: 2, 4: 5})
  
        (dice, constant) = rpg_utils.parse_dice_string('15')
        self.assertEqual(constant, 15)
        self.assertEqual(dice, {})
  
        self.assertRaises(RuntimeError, rpg_utils.parse_dice_string, '+1d2+1')
        self.assertRaises(RuntimeError, rpg_utils.parse_dice_string, '1d2+1+')
        self.assertRaises(RuntimeError, rpg_utils.parse_dice_string, '1d-1')
        self.assertRaises(RuntimeError, rpg_utils.parse_dice_string, 'd20+1')

    def test_Stat_rolls_min(self):
        'Tests that Stat()s can be created and roll the correct min'

        with AlternateRandom(minimum=True):
            s = rpg_utils.Stat({5: 2}, 2)
            self.assertEqual(s.roll(), 4)
            self.assertEqual(s.roll(modifier=-10, minimum=0), 0)
            s = rpg_utils.Stat.from_dice_string('2d+1')
            self.assertEqual(s.roll(), 3)

    def test_Stat_rolls_max(self):
        'Tests that Stat()s can be created and roll the correct max'

        with AlternateRandom(maximum=True):
            s = rpg_utils.Stat({5: 2}, 2)
            self.assertEqual(s.roll(), 12)
            self.assertEqual(s.roll(modifier=-10, minimum=0), 2)
            s = rpg_utils.Stat.from_dice_string('2d+1')
            self.assertEqual(s.roll(), 13)


if __name__ == '__main__':
  unittest.main()

