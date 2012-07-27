from mudpy.utils.execfile import execfile

import os

from socket import AF_INET, AF_INET6

class ConfigGroup: pass

db = ConfigGroup()
db.path = None

log = ConfigGroup()
log.level = 'INFO'
log.time_format = '%Y%m%d %H:%M:%S'
log.append_time_fraction = '.%03f'

telnet = ConfigGroup()
telnet.address_family = AF_INET6
telnet.bind_address = ''
telnet.bind_port = 8888
telnet.terminal_type_support = True
telnet.utf8_support = True
telnet.window_size_support = True
telnet.readoptions_sleep_time = 0.5

term = ConfigGroup()
term.color_types = {
    'ansi',
    'cygwin',
    'Eterm',
    'linux',
    'mach',
    'pcansi',
    'rxvt',
    'screen',
    'vt100',
    'vt102',
    'vt220',
    'xterm',
}

player = ConfigGroup()
player.default_aliases = {
    'north' : 'go north',
    'south' : 'go south',
    'east'  : 'go east',
    'west'  : 'go west',
    'up'    : 'go up',
    'down'  : 'go down',
    
    'n'     : 'go north',
    's'     : 'go south',
    'e'     : 'go east',
    'w'     : 'go west',
    
    'northeast' : 'go northeast',
    'northwest' : 'go northwest',
    'southeast' : 'go southeast',
    'southwest' : 'go southwest',

    'l' : 'look',
}

def load(cfg_file):
    execfile(cfg_file, globals(), globals())

