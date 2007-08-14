from string import Template


# CODES:
ESC                   = chr(27)
RESET                 = ESC + '[0m'
BOLD_ON               = ESC + '[1m'
ITALICS_ON            = ESC + '[3m'
UNDERLINE_ON          = ESC + '[4m'
BLINK_ON              = ESC + '[5m'
INVERSE_ON            = ESC + '[7m'
INVISIBLE_ON          = ESC + '[8m'
STRIKETHROUGH_ON      = ESC + '[9m'
BOLD_OFF              = ESC + '[22m'
ITALICS_OFF           = ESC + '[23m'
UNDERLINE_OFF         = ESC + '[24m'
BLINK_OFF             = ESC + '[25m'
INVERSE_OFF           = ESC + '[27m'
STRIKETHROUGH_OFF     = ESC + '[29m'
BLACK                 = ESC + '[30m' + BOLD_OFF
RED                   = ESC + '[31m' + BOLD_OFF
GREEN                 = ESC + '[32m' + BOLD_OFF
YELLOW                = ESC + '[33m' + BOLD_OFF
BLUE                  = ESC + '[34m' + BOLD_OFF
MAGENTA               = ESC + '[35m' + BOLD_OFF
CYAN                  = ESC + '[36m' + BOLD_OFF
WHITE                 = ESC + '[37m' + BOLD_OFF
DEFAULT               = ESC + '[39m' + BOLD_OFF
BRIGHT_BLACK          = ESC + '[30m' + BOLD_ON
BRIGHT_RED            = ESC + '[31m' + BOLD_ON
BRIGHT_GREEN          = ESC + '[32m' + BOLD_ON
BRIGHT_YELLOW         = ESC + '[33m' + BOLD_ON
BRIGHT_BLUE           = ESC + '[34m' + BOLD_ON
BRIGHT_MAGENTA        = ESC + '[35m' + BOLD_ON
BRIGHT_CYAN           = ESC + '[36m' + BOLD_ON
BRIGHT_WHITE          = ESC + '[37m' + BOLD_ON
BRIGHT_DEFAULT        = ESC + '[39m' + BOLD_ON
BG_BLACK              = ESC + '[40m'
BG_RED                = ESC + '[41m'
BG_GREEN              = ESC + '[42m'
BG_YELLOW             = ESC + '[43m'
BG_BLUE               = ESC + '[44m'
BG_MAGENTA            = ESC + '[45m'
BG_CYAN               = ESC + '[46m'
BG_WHITE              = ESC + '[47m'
BG_DEFAULT            = ESC + '[49m'
CLEARSCREEN           = ESC + '[2J' + ESC + '[1;1H'

del ESC

current_locals = locals().copy()
ANSI_MAP = dict([(x, current_locals[x]) for x in current_locals if x[0] != '_'])
del current_locals

DEFAULT_MAP = dict([(x, '') for x in ANSI_MAP.keys()])


def map_string(s, map = DEFAULT_MAP):
  t = Template(s)
  return t.safe_substitute(map)


if __name__ == '__main__':
  strings = list()
  strings.append('${BG_WHITE}${BLACK}This is black${RESET}')
  strings.append('${RED}This is red${RESET}')
  strings.append('${GREEN}This is green${RESET}')
  strings.append('${YELLOW}This is yellow${RESET}')
  strings.append('${BLUE}This is blue${RESET}')
  strings.append('${MAGENTA}This is magenta${RESET}')
  strings.append('${CYAN}This is cyan${RESET}')
  strings.append('${WHITE}This is white${RESET}')
  strings.append('${DEFAULT}This is default${RESET}')
  strings.append('${BG_WHITE}${BRIGHT_BLACK}This is bright black${RESET}')
  strings.append('${BRIGHT_RED}This is bright red${RESET}')
  strings.append('${BRIGHT_GREEN}This is bright green${RESET}')
  strings.append('${BRIGHT_YELLOW}This is bright yellow${RESET}')
  strings.append('${BRIGHT_BLUE}This is bright blue${RESET}')
  strings.append('${BRIGHT_MAGENTA}This is bright magenta${RESET}')
  strings.append('${BRIGHT_CYAN}This is bright cyan${RESET}')
  strings.append('${BRIGHT_WHITE}This is bright white${RESET}')
  strings.append('${BRIGHT_DEFAULT}This is bright default${RESET}')
  strings.append('${BG_BLACK}This is a black background${RESET}')
  strings.append('${BG_RED}This is a red background${RESET}')
  strings.append('${BG_GREEN}This is a green background${RESET}')
  strings.append('${BG_YELLOW}This is a yellow background${RESET}')
  strings.append('${BG_BLUE}This is a blue background${RESET}')
  strings.append('${BG_MAGENTA}This is a magenta background${RESET}')
  strings.append('${BG_CYAN}This is a cyan background${RESET}')
  strings.append('${BG_WHITE}${BLACK}This is a white background${RESET}')
  strings.append('${BG_DEFAULT}This is a default background${RESET}')

  for s in strings:
    print map_string(s, ANSI_MAP)

