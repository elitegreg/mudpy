from mudpy.utils.execfile import execfile

import os

from socket import AF_INET, AF_INET6

class ConfigGroup: pass

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

execfile(os.getenv('MUDPY_CONFIG_FILE', 'mudconfig.py'), globals(), locals())

