from mudpy.mudlib.command import *

def quit_cmd(cmd, requestor):
    if cmd != 'quit':
        raise CommandError('@quit takes no arguments.')

    requestor.save()
    requestor.write('Goodbye!')
    requestor.disconnect()


register_gameplay_command('quit', quit_cmd)

