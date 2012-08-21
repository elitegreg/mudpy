from mudpy.english import *

import unittest


class EnglishTest(unittest.TestCase):
    def test_add_article(self):
        self.assertEqual(add_article('house'), 'a house')
        self.assertEqual(add_article('house', True), 'the house')
        self.assertEqual(add_article('apple'), 'an apple')
        self.assertEqual(add_article('Eskimo'), 'an Eskimo')

    def test_remove_article(self):
        self.assertEqual(remove_article('food'), 'food')
        self.assertEqual(remove_article('an animal'), 'animal')
        self.assertEqual(remove_article('A Balloon'), 'Balloon')
        self.assertEqual(remove_article('the school'), 'school')

    def test_item_list(self):
        self.assertEqual(item_list(['ball', 'cup', 'pencil', 'paper']), 'ball, cup, pencil and paper')

    def test_possessive_noun(self):
        self.assertEqual(possessive_noun('Greg'), "Greg's")
        self.assertEqual(possessive_noun('Rees'), "Rees'")
        self.assertEqual(possessive_noun('Stax'), "Stax'")
        self.assertEqual(possessive_noun('Baz'), "Baz'")

    def test_possessive_pronoun(self):
        self.assertEqual(possessive_pronoun('male'), 'his')
        self.assertEqual(possessive_pronoun('female'), 'her')
        self.assertEqual(possessive_pronoun('neutral'), 'hir')
        self.assertEqual(possessive_pronoun('unknown'), 'its')

    def test_nominative(self):
        self.assertEqual(nominative('male'), 'he')
        self.assertEqual(nominative('female'), 'she')
        self.assertEqual(nominative('neutral'), 'sie')
        self.assertEqual(nominative('unknown'), 'it')

    def test_objective(self):
        self.assertEqual(objective('male'), 'him')
        self.assertEqual(objective('female'), 'her')
        self.assertEqual(objective('neutral'), 'hir')
        self.assertEqual(objective('unknown'), 'it')

    def test_reflexive(self):
        self.assertEqual(reflexive('male'), 'himself')
        self.assertEqual(reflexive('female'), 'herself')
        self.assertEqual(reflexive('neutral'), 'hirself')
        self.assertEqual(reflexive('unknown'), 'itself')

    def test_pluralize(self):
        self.assertEqual(pluralize(''), '')
        self.assertEqual(pluralize('moose'), 'moose')
        self.assertEqual(pluralize('stash'), 'stashes')
        self.assertEqual(pluralize('staff'), 'staves')
        self.assertEqual(pluralize('self'), 'selves')
        self.assertEqual(pluralize('clef'), 'clefs')
        self.assertEqual(pluralize('bacterium'), 'bacteria')
        self.assertEqual(pluralize('fungus'), 'fungi')
        self.assertEqual(pluralize('bus'), 'buses')
        self.assertEqual(pluralize('bum'), 'bums')
        self.assertEqual(pluralize('story'), 'stories')

    def test_cardinal(self):
        self.assertEqual(cardinal(-69), 'negative sixty-nine')
        self.assertEqual(cardinal(-1), 'negative one')
        self.assertEqual(cardinal(0), 'zero')
        self.assertEqual(cardinal(-0), 'zero')
        self.assertEqual(cardinal(15), 'fifteen')
        self.assertEqual(cardinal(100), 'one hundred')
        self.assertEqual(cardinal(1000), 'one thousand')
        self.assertEqual(cardinal(-9999999999999), 'less than negative a trillion')
        self.assertEqual(cardinal(9999999999999), 'more than a trillion')
        self.assertEqual(cardinal(123971888562), 'one hundred twenty-three billion nine hundred seventy-one million eight hundred eighty-eight thousand five hundred sixty-two')
        self.assertEqual(cardinal(-123971888562), 'negative one hundred twenty-three billion nine hundred seventy-one million eight hundred eighty-eight thousand five hundred sixty-two')
        self.assertEqual(cardinal(5000), 'five thousand')


if __name__ == '__main__':
  unittest.main()

