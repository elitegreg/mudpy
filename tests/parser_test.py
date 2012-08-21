from mudpy.english import pluralize
from mudpy.parser import Parser, register_with_parser

import unittest


'This is the help string'


class Object:
    __slots__ = ('short', 'nouns', 'adjectives', 'plurals', 'living')
    def __init__(self, **kwargs):
        self.living = False
        for k, v in kwargs.items():
            setattr(self, k, v)
        assert(self.nouns is not None)
        assert(self.adjectives is not None)
        if getattr(self, 'plurals', None) is None:
            self.plurals = [pluralize(x) for x in self.nouns]

    def __repr__(self):
        return self.short

    # emulate weakref
    def __call__(self):
        return self

    @property
    def environment(self):
        return None


@register_with_parser()
def get_OBS(requestor, direct_obj):
    requestor.result = ('get', set(direct_obj))

def can_get_OBS(requestor):
    return True

@register_with_parser()
def get_OBS_from_OBJ(requestor, direct_obj, indirect_obj):
    requestor.result = ('get', set(direct_obj), indirect_obj)

@register_with_parser()
def look(requestor):
    requestor.result = ('look',)

@register_with_parser()
def look_at_OBJ(requestor, direct_obj):
    requestor.result = ('look at', direct_obj)

@register_with_parser()
def look_at_OBJ_in_OBJ(requestor, direct_obj, indirect_obj):
    requestor.result = ('look at', direct_obj, indirect_obj)


class Player:
    result = None
    def deep_inventory(self):
        return self.objs


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

        self.redball = Object(short='Red Ball', nouns=['ball', 'thing'], adjectives=['red', 'round'])
        self.greenball = Object(short='Green Ball', nouns=['ball', 'thing'], adjectives=['green', 'round'])
        self.bag = Object(short='Bag', nouns=['bag'], adjectives=[])

        self.player = Player()
        self.player.objs = [self.redball, self.greenball, self.bag]

    def testHelp(self):
        help = globals()['__doc__']
        self.assertEqual(help, self.parser.help('get'))
        self.assertEqual(help, self.parser.help('look'))
        self.assertRaises(KeyError, self.parser.help, 'foo')

    def testGetOBS(self):
        self.parser.parse_sentence('get red ball', self.player)
        self.assertEqual(self.player.result, ('get', {self.redball}))
        self.player.result = None
        self.parser.parse_sentence('get balls', self.player)
        self.assertEqual(self.player.result, ('get', set([self.greenball, self.redball])))
        self.player.result = None
        self.parser.parse_sentence('get all of the balls', self.player)
        self.assertEqual(self.player.result, ('get', set([self.greenball, self.redball])))
        self.player.result = None
        self.parser.parse_sentence('get balls from bag', self.player)
        self.assertEqual(self.player.result, ('get', set([self.greenball, self.redball]), self.bag))
        self.player.result = None
        self.parser.parse_sentence('get all from bag', self.player)
        self.assertEqual(self.player.result, ('get', set([self.greenball, self.redball, self.bag]), self.bag))

    def testLook(self):
        self.parser.parse_sentence('look', self.player)
        self.assertEqual(self.player.result, ('look',))

    def testLookAtObj(self):
        self.parser.parse_sentence('look at bag', self.player)
        self.assertEqual(self.player.result, ('look at', self.bag))

    def testLookAtObjInObj(self):
        self.parser.parse_sentence('look at a red ball in the bag', self.player)
        self.assertEqual(self.player.result, ('look at', self.redball, self.bag))
        self.player.result = None
        self.parser.parse_sentence('look at green round ball in the bag', self.player)
        self.assertEqual(self.player.result, ('look at', self.greenball, self.bag))

    def testInvalidCmd(self):
        error = None
        try:
            self.parser.parse_sentence('yell Hello World!', self.player)
        except Exception as e:
            error = str(e)
        self.assertEqual(error, 'What?')
        self.assertEqual(self.player.result, None)
    
    def testValidCmdUnknownParams(self):
        error = None
        try:
            self.parser.parse_sentence('look at foobar', self.player)
        except Exception as e:
            error = str(e)
        self.assertEqual(error, 'That is not here.')
        self.assertEqual(self.player.result, None)


if __name__ == '__main__':
  unittest.main()

