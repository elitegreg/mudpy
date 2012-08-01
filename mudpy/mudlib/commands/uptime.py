from mudpy.mudlib.command import *

import datetime

__starttime = datetime.datetime.now()


def uptime_cmd(cmd, requestor):
    if cmd != '@uptime':
        raise CommandError('@uptime takes no arguments.')

    now = datetime.datetime.now()

    diff = now - __starttime

    days = diff.days
    hrs  = int(diff.seconds // 3600)
    mins = int(diff.seconds // 60 % 60)

    if days > 0:
        msg = 'Up {} days {} hours and {} minutes.'.format(days, hrs, mins)
    elif hrs > 0:
        msg = 'Up {} hours and {} minutes.'.format(hrs, mins)
    else:
        msg = 'Up {} minutes.'.format(mins)

    requestor.write(msg)


register_system_command('@uptime', uptime_cmd)

