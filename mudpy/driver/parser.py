import re

DEFAULT_ARTICLES = 'a,an,the'
DEFAULT_PREPOSITIONS = 'at,from,in,on,to,with'

VERB = '(?:(?P<verb>\w+)(?:\s+(?P<verbprep>%s))?)'

# %s arguments are VERB, PREPOSITIONS
PARSER_RE = '^%s(?:\s+(?P<direct_obj>.*?))?(?(direct_obj)%s\s+(?P<indirect_obj>.*))?$'


class Parser(object):
  def __init__(config):
    self.__articles = set(config.get('parser', 'articles',
        DEFAULT_ARTICLES).split(','))
    self.__prepositions = set(config.get('parser', 'prepositions',
        DEFAULT_PREPOSITIONS).split(','))
    prep_regex = '\s+(?<prep>%s)' % '|'.join(self.__prepositions)
    verb_regex = VERB % '|'.join(self.__prepositions)
    self.__regex = PARSER_RE % (verb_regex, prep_regex)
    self.__parser = re.compile(PARSER_RE)

  def parse_components(self, msg):
    match_object = self.__parser.match(msg)
    if match_object:
      return match_object.groupdict()
    return None

  def parse_command(self, cmd, inventories):
    components = self.parse_components(cmd)
    if components is None:
      return None
    
