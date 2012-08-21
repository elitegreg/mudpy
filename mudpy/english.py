import re

_article_regex = re.compile(r'(the|a|an)\s+(.*)', re.IGNORECASE)
_possessive_pronouns = dict(male='his', female='her', neutral='hir')
_nominative_pronouns = dict(male='he', female='she', neutral='sie')
_objective_pronouns = dict(male='him', female='her', neutral='hir')
_abnormal_plurals = dict(
    moose='moose',
    mouse='mice',
    die='dice',
    index='indices',
    human='humans',
    sheep='sheep',
    fish='fish',
    child='children',
    ox='oxen',
    tooth='teeth',
    deer='deer',
    sphinx='sphinges')
_cardinals = {
    0: 'zero',
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
    6: 'six',
    7: 'seven',
    8: 'eight',
    9: 'nine',
    10: 'ten',
    11: 'eleven',
    12: 'twelve',
    13: 'thirteen',
    14: 'fourteen',
    15: 'fifteen',
    16: 'sixteen',
    17: 'seventeen',
    18: 'eighteen',
    19: 'nineteen',
    20: 'twenty',
    30: 'thirty',
    40: 'fourty',
    50: 'fifty',
    60: 'sixty',
    70: 'seventy',
    80: 'eighty',
    90: 'ninety',
    100: 'one hundred',
    1000: 'one thousand',
    1000000: 'one million',
    1000000000: 'one billion',
    1000000000000: 'one trillion',
}

for i in range(21, 100):
    (tens, ones) = divmod(i, 10)
    if ones:
        tens = _cardinals[tens*10]
        ones = _cardinals[ones]
        _cardinals[i] = '{}-{}'.format(tens, ones)



def add_article(s, definite=False):
    if definite:
        return 'the {}'.format(remove_article(s))

    if s[0] in 'AEIOUaeiou':
        return 'an {}'.format(s)
    else:
        return 'a {}'.format(s)


def remove_article(s):
    mo = _article_regex.match(s)

    if mo:
        return mo.group(2)
    return s


def item_list(lst):
    return '{} and {}'.format(', '.join(lst[0:-1]), lst[-1])


def possessive_noun(noun):
    if noun[-1] in 'sxz':
        return "{}'".format(noun)
    return "{}'s".format(noun)


def possessive_pronoun(gender):
    return _possessive_pronouns.get(gender.lower(), 'its')


def nominative(gender):
    return _nominative_pronouns.get(gender.lower(), 'it')


def objective(gender):
    return _objective_pronouns.get(gender.lower(), 'it')


def reflexive(gender):
    return "{}self".format(objective(gender))


def pluralize(noun):
    if not len(noun):
        return noun

    lower_noun = noun.lower()

    try:
        return _abnormal_plurals[lower_noun]
    except KeyError:
        pass

    last2 = lower_noun[-2:]

    if last2 == 'ch' or last2 == 'sh':
        return '{}es'.format(noun)
    elif last2 == 'ff' or last2 == 'fe':
        return '{}ves'.format(noun[0:-2])
    elif last2 == 'us' and len(noun) > 3:
        return '{}i'.format(noun[0:-2])
    elif last2 == 'um' and len(noun) > 3:
        return '{}a'.format(noun[0:-2])
    elif last2 == 'ef':
        return '{}s'.format(noun)

    if lower_noun[-1] in 'oxs':
        return '{}es'.format(noun)
    elif lower_noun[-1] == 'f':
        return '{}ves'.format(noun[0:-1])
    elif lower_noun[-1] == 'y':
        if lower_noun[-2] not in 'abcde':
            return '{}ies'.format(noun[0:-1])

    return '{}s'.format(noun)


def cardinal(x):
    negative = ''

    if x < 0:
        negative = "negative "
        x = abs(x)

    try:
        result = _cardinals[x]
        return '{}{}'.format(negative, result)
    except KeyError:
        pass

    if x > 1000000000000:
        if len(negative):
            return 'less than negative a trillion'
        return 'more than a trillion'

    for base in (1000000000, 1000000, 1000, 100):
        if x >= base:
            (a, x) = divmod(x, base)
            basestr = _cardinals[base].split()[-1]
            if x:
                return '{}{} {} {}'.format(negative, cardinal(a), basestr, cardinal(x))
            else:
                return '{}{} {}'.format(negative, cardinal(a), basestr)

