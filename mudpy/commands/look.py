from mudpy.command import *

def look_cmd(cmd, requestor):
    if cmd.startswith('look at'):
        raise NotImplemented

    if cmd != 'look':
        raise CommandError('Syntax error')

    env = requestor.environment
    longdesc = env.long_description

    requestor.write(longdesc)


register_gameplay_command('look', look_cmd)

