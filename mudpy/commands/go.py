from mudpy.command import *
from mudpy.object import *

from .look import look_cmd

def go_cmd(cmd, requestor):
    if cmd == 'go':
        raise CommandError('Go where?')
    where = cmd[2:].lstrip()
    env = requestor.environment
    
    try:
        exit = env.get_exit(where)
        move_object(requestor, exit) 
        look_cmd('look', requestor)
    except KeyError:
        raise CommandError('There is no exit "{}"'.format(where))


register_gameplay_command('go', go_cmd)

