from mudpy import logging
from mudpy.utils.borg import Borg
from mudpy.utils.enum import Enum

#logging.CURRENT_LOG_LEVEL = logging.TRACE

from collections import defaultdict, namedtuple

import copy
import operator

# TODO
# * Plurals
# * Livings
# * Ordinals
# * "my" objects - treat my as adj and add each object my adj if obj.env == requestor
# * callbacks
#   * can_verb..() -> only singular: get OBS from OBJ -> can_get_OBJ_from_OBJ -> true/false. Applies to player.
#   * direct_look_at_obj
#   * direct_look_at_obj_in_obj
#   * indirect_look_at_obj_in_obj 
#   * don't forget liv versions
# * "Jabba the Hutt" doesn't parse with Jabba as a noun

SW = Enum('ARTICLE SELF ORDINAL ALL')

SpecialWord = namedtuple('SpecialWord', ('swtype', 'ordinal'))

Specials = {
    'the'     : SpecialWord(SW.ARTICLE, None),
    'me'      : SpecialWord(SW.SELF, None),
    'myself'  : SpecialWord(SW.SELF, None),
    'all'     : SpecialWord(SW.ALL, None),

    'a'       : SpecialWord(SW.ORDINAL, 1),
    'an'      : SpecialWord(SW.ORDINAL, 1),

    'first'   : SpecialWord(SW.ORDINAL, 1),
    'second'  : SpecialWord(SW.ORDINAL, 2),
    'third'   : SpecialWord(SW.ORDINAL, 3),
    'fourth'  : SpecialWord(SW.ORDINAL, 4),
    'fifth'   : SpecialWord(SW.ORDINAL, 5),
    'sixth'   : SpecialWord(SW.ORDINAL, 6),
    'seventh' : SpecialWord(SW.ORDINAL, 7),
    'eighth'  : SpecialWord(SW.ORDINAL, 8),
    'nineth'  : SpecialWord(SW.ORDINAL, 9),
    'tenth'   : SpecialWord(SW.ORDINAL, 10),

    '1st'     : SpecialWord(SW.ORDINAL, 1),
    '2nd'     : SpecialWord(SW.ORDINAL, 2),
    '3rd'     : SpecialWord(SW.ORDINAL, 3),
    '4th'     : SpecialWord(SW.ORDINAL, 4),
    '5th'     : SpecialWord(SW.ORDINAL, 5),
    '6th'     : SpecialWord(SW.ORDINAL, 6),
    '7th'     : SpecialWord(SW.ORDINAL, 7),
    '8th'     : SpecialWord(SW.ORDINAL, 8),
    '9th'     : SpecialWord(SW.ORDINAL, 9),
    '10th'    : SpecialWord(SW.ORDINAL, 10),
}

Literals = frozenset(
    'in into with without into for on under against out within '
    'of from between at to over near inside onto off through '
    'across up down every around about only here room exit '
    'enter'.split())

Tokens = Enum('LIT_TOKEN STR_TOKEN WRD_TOKEN OBJ_TOKEN LIV_TOKEN OBS_TOKEN LVS_TOKEN')

TokenDefs = dict(
    OBJ=Tokens.OBJ_TOKEN,
    STR=Tokens.STR_TOKEN,
    WRD=Tokens.WRD_TOKEN,
    LIV=Tokens.LIV_TOKEN,
    OBS=Tokens.OBS_TOKEN,
    LVS=Tokens.LVS_TOKEN)


class Verb:
    __slots__ = ('name', 'rule_str', 'handler_func', 'weight', 'lits', 'tokens', 'count_objs', 'help', 'namespace')

    def __repr__(self):
        return 'Verb(name={},weight={},lits={},tokens={},handler_func={})'.format(
            self.name, self.weight, self.lits, self.tokens, self.handler_func)

    def check_can(self, requestor):
        return self.namespace['can_{}'.format(self.rule_str)](requestor)

    def check_direct(self, requestor, direct_obj, indirect_obj=None):
        if indirect_obj:
            args = (requestor, indirect_obj)
        else:
            args = (requestor, )
        return getattr(direct_obj, 'direct_{}'.format(self.rule_str))(*args)

    def check_indirect(self, requestor, direct_obj, indirect_obj):
        return getattr(indirect_obj, 'indirect_{}'.format(self.rule_str))(requestor, direct_obj)


class Words:
    __slots__ = ('words', 'fragments')

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)

    def __repr__(self):
        return 'Words(words={},fragments={}'.format(
            self.words, self.fragments)


class ParserError(RuntimeError):
    def __init__(self, err='What?'):
        super().__init__(err)


class ErrIncomplete(ParserError):
    def __init__(self):
        super().__init__('Incomplete request.')


class ErrIsNotHere(ParserError):
    def __init__(self):
        super().__init__('That is not here.')


class ErrNotLiving(ParserError):
    def __init__(self):
        super().__init__('That is not alive.')


class ErrAmbiguous(ParserError):
    def __init__(self):
        super().__init__('That is ambiguous.')


class ErrBadMultiple(ParserError):
    def __init__(self):
        super().__init__('Bad multiple.')


class ErrBadOrdinal(ParserError):
    def __init__(self):
        super().__init__('Bad ordinal.')


class ErrLiteral(ParserError):
    def __init__(self, lit):
        super().__init__('Expected literal "{}"'.format(lit))


class State: 
    def __init__(self, requestor, words):
        self.requestor = requestor
        self.words = words
        self.objs = None
        self.nouns = None
        self.adjs = None
        self.plurals = None
        self.matches = list()

    def reset(self, verb):
        self.verb = verb
        self.current_lit = 0
        del self.matches[:]

        if self.objs is None and verb.count_objs > 0:
            self.__load_objects()

    def __load_objects(self):
        self.objs = frozenset(self.requestor.deep_inventory())
        self.nouns = defaultdict(set)
        self.adjs = defaultdict(set)
        self.plurals = defaultdict(set)
        for obj in self.objs:
            for noun in obj.nouns:
                self.nouns[noun].add(obj)
            for adj in obj.adjectives:
                self.adjs[adj].add(obj)
            for plural in obj.plurals:
                self.plurals[plural].add(obj)

            # support "my sword", etc.
            if obj().environment is self.requestor:
                self.adjs['my'].add(obj)
        self.nouns.default_factory = None
        self.adjs.default_factory = None
        self.plurals.default_factory = None


def peek(iterator, default=None):
    try:
        return next(copy.deepcopy(iterator)) # TODO copy.copy()?
    except StopIteration:
        return default


class Parser(Borg):
    def help(self, verb):
        return self.__verbs[verb][0].help

    def dump_rules(self):
        for list_of_verbs in self.__verbs.values():
            for verb in list_of_verbs:
                print(verb)

    def add_rule(self, rule_str, rule, handler, namespace, system_command=False, help=None):
        verb, *rule = rule.split()
        v = Verb()
        v.name = '@{}'.format(verb) if system_command else verb
        v.weight = 1
        v.lits = []
        v.tokens = []
        v.help = help
        v.namespace = namespace
        v.rule_str = rule_str
        self.__parse_rule_definition(v, rule)
        v.count_objs = sum((1 for t in v.tokens if t >= Tokens.OBJ_TOKEN))
        v.handler_func = handler
        try:
            l = self.__verbs.setdefault(v.name, list())
            l.append(v)
            l.sort(key=operator.attrgetter('weight'), reverse=True)
        except AttributeError:
            self.__verbs = { v.name : [v] }

    def parse_sentence(self, sentence, requestor):
        logging.debug('parser::parse_sentence {}', sentence) 
        words = self.__parse_sentence_into_words(sentence)

        if len(words) == 0:
            return 

        worditer = iter(enumerate(words.words))

        try:
            verb = next(worditer)[1]
            verbmatches = self.__verbs[verb]
        except KeyError:
            logging.debug('parser::verb {} not found', verb)
            raise ParserError()

        state = State(requestor, words)
        errors = list()

        for verb in verbmatches:
            logging.debug('parser::trying to parse using: {}', verb)
            state.reset(verb)
            result = self.__parse_rule(copy.deepcopy(worditer), state)

            if result:
                errors.append(result)
                continue

            #result = verb.check_can(requestor)
            #if type(result) is str:
                #errors.append(result)
                #continue

            matches = [x[0] for x in state.matches]

            if verb.count_objs == 0:
                logging.debug('parser::calling handler with {}', matches)
                state.verb.handler_func(requestor, *matches)
                return
            elif verb.count_objs == 1:
                for (objs, token, ordinal) in state.matches:
                    if token < Tokens.OBJ_TOKEN:
                        continue
                    plural = (token >= Tokens.OBS_TOKEN)
                    objs = {x for x in objs if verb.check_direct(requestor, x)}
                    if len(objs) == 0:
                        continue
            elif verb.count_objs == 2:
                pass

        assert(len(errors) > 0)
        raise errors[0]

        # more to go...

    def __parse_obj(self, worditer, token, state):
        # returns (objs, ordinal)
        ordinal = 0
        plural = False
        no_self = False

        objs = set(state.objs)

        for wordidx, word in worditer:
            logging.debug('parser::__parse_obj: word = {}', word)

            if len(objs) == 0:
                logging.debug('parser::__parse_obj: no objects remaining')
                return None, ordinal

            try:
                spec = Specials[word]
                logging.debug('parser::__parse_obj: found special word {}', spec.swtype)

                if spec.swtype == SW.ARTICLE:
                    continue
                elif spec.swtype == SW.ALL:
                    if ordinal:
                        logging.debug('parser::__parse_obj: "all" used after ordinal')
                        return ErrBadMultiple()

                    if token < Tokens.OBS_TOKEN: # Token only matches singular
                        logging.debug('parser::__parse_obj: "all" used for singular object token')
                        return ErrBadMultiple()

                    wordidx, word = peek(worditer, (None, None))

                    if word == 'of':
                        logging.debug('parser::__parse_obj: "all of" found')
                        wordidx, word = next(worditer)
                        plural = True
                        continue
                    else:
                        logging.debug('parser::__parse_obj: "all" found')
                        return state.objs.copy(), ordinal
                elif spec.swtype == SW.ORDINAL:
                    if ordinal == 0 and not plural:
                        ordinal = spec.ordinal
                        continue
                    # might be an adjective, so flow through ?
                elif spec.swtype == SW.SELF:
                    if no_self:
                        logging.debug('parser::__parse_obj: "me" used with leading words')
                        return None, ordinal
                    return {state.requestor}, ordinal
                else:
                    raise NotImplementedError
            except KeyError:
                pass

            # "me" may only be used in a 1 word object parse
            no_self = True

            living = (token == Tokens.LIV_TOKEN or token == Tokens.LVS_TOKEN)

            if not plural: 
                try:
                    o = state.nouns[word]
                except KeyError:
                    pass
                else:
                    # TODO flag this is a singular result! in case this returns multiple objs for a OBS_TOKEN
                    logging.debug('parser::__parse_obj: found noun {}, reducing objects and returning', word)
                    objs.intersection_update(o)
                    if living:
                        objs.difference_update({x for x in objs if not getattr(x, 'living', False)})
                        if len(objs) == 0:
                            return ErrNotLiving()
                    return objs, ordinal

            if token >= Tokens.OBS_TOKEN and ordinal == 0:
                try:
                    o = state.plurals[word]
                except KeyError:
                    pass
                else:
                    logging.debug('parser::__parse_obj: found plural {}, reducing objects and returning', word)
                    objs.intersection_update(o)
                    if living:
                        objs.difference_update({x for x in objs if not getattr(x, 'living', False)})
                        if len(objs) == 0:
                            return ErrNotLiving()
                    return objs, ordinal

            try:
                o = state.adjs[word]
            except KeyError:
                logging.debug('parser::__parse_obj: not an adjective {}, returning not found', word)
                return ErrIsNotHere()
            else:
                logging.debug('parser::__parse_obj: found adjective {}, reducing objects', word)
                objs.intersection_update(o)

        logging.debug('parser::__parse_obj: out of words, returning not found')
        return ErrIncomplete()

    def __parse_rule(self, worditer, state):
        for tokenidx, token in enumerate(state.verb.tokens):
            try:
                logging.debug('parser::token = {}', token)
                if token >= Tokens.OBJ_TOKEN:
                    result = self.__parse_obj(worditer, token, state)

                    if type(result) == tuple:
                        (objs, ordinal) = result
                    else:
                        logging.debug('parser:failed to parse obj')
                        return result

                    state.matches.append((objs, token, ordinal))
                    logging.debug('parser:found object/s')
                elif token == Tokens.STR_TOKEN:
                    if len(state.verb.tokens) == tokenidx + 1:
                        wordidx, word = next(worditer)
                        state.matches.append((words.fragments[wordidx - 1], Tokens.STR_TOKEN, None))
                        logging.debug('parser:found string "{}"', words.fragments[wordidx -1])
                    else:
                        # rule where STR_TOKEN is not the last token!
                        s = []
                        for wordidx, word in worditer:
                            if word != state.verb.lits[state.current_lit]:
                                s.append(word)
                        if len(s) > 0:
                            state.matches.append((word, Tokens.LIT_TOKEN, None))
                            state.current_lit += 1
                            state.matches.append((' '.join(s), Tokens.STR_TOKEN, None))
                            logging.debug('parser:found string "{}"', ' '.join(s))
                        else:
                            return ErrIncomplete()
                elif token == Tokens.WRD_TOKEN:
                    wordidx, word = next(worditer)
                    state.matches.append((word, Tokens.WRD_TOKEN, None))
                    logging.debug('parser:found word "{}"', word)
                elif token == Tokens.LIT_TOKEN:
                    wordidx, word = next(worditer)
                    if state.verb.lits[state.current_lit] == word:
                        state.matches.append((word, Tokens.LIT_TOKEN, None))
                        state.current_lit += 1
                        logging.debug('parser:found literal "{}"', word)
                    else:
                        return ErrLiteral(state.verb.lits[state.current_lit])
            except StopIteration:
                return ErrIncomplete()

        try:
            next(worditer)
            logging.debug('parser:not all words were parsed')
            return ErrIncomplete()
        except StopIteration:
            pass

    def __parse_sentence_into_words(self, sentence):
        w = Words()
        w.words = sentence.split()
        w.fragments = list()
        for i in range(1, len(w.words)):
            w.fragments.append(sentence.split(None, i)[-1])
        return w

    def __parse_rule_definition(self, verb, rule):
        objs = 0

        has_plural = False

        for word in rule:
            if word in Literals:
                if len(verb.lits) == 2:
                    raise ParserError(
                        'Too many literals in rule "{} {}"'.format(verb, rule))
                verb.lits.append(word)
                verb.tokens.append(Tokens.LIT_TOKEN)
                verb.weight += 1
            else:
                try:
                    token = TokenDefs[word]

                    if token >= Tokens.OBJ_TOKEN:
                        # is obj
                        objs += 1
                        if objs > 2:
                            raise ParserError(
                                'Too many objects in rule "{} {}"'.format(verb, rule))
                        verb.weight += 2

                        if token >= Tokens.OBS_TOKEN:
                            if has_plural:
                                raise ParserError('Only one plural token allowed per rule')
                            has_plural = True
                            verb.weight -= 1
                        if token in (Tokens.LIV_TOKEN, Tokens.LVS_TOKEN):
                            verb.weight += 1

                    verb.weight += 1
                except KeyError:
                    raise ParserError('Unknown token "{}" in rule "{} {}"'.format(word, verb, rule))
                verb.tokens.append(token)

            if Tokens.STR_TOKEN in verb.tokens:
                try:
                    idx = 0
                    while True:
                        idx = verb.tokens.index(Tokens.STR_TOKEN, idx)
                        if idx != len(verb.tokens) - 1:
                            if verb.tokens[idx+1] != Tokens.LIT_TOKEN:
                                raise ParserError('A STR token may only be followed by a literal in rule "{} {}"'.format(verb, rule))
                except ValueError:
                    pass 


class register_with_parser:
    def __init__(self, system_command=False):
        self.__system_command = system_command

    def __call__(self, func):
        namespace = func.__globals__
        if func.__doc__ is not None:
            help = func.__doc__
        else:
            # module documentation
            help = namespace['__doc__']
        Parser().add_rule(func.__name__, func.__name__.replace('_', ' '), func, namespace, self.__system_command, help)
        return func

