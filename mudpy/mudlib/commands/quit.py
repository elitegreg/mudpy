from mudpy.mudlib.command import register_gameplay_command

def quit_cmd(cmd, requestor):
    requestor.save()
    requestor.write('Goodbye!')
    requestor.disconnect()


register_gameplay_command('quit', quit_cmd)

