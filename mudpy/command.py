from mudpy import logging

import pprint


__all__ = [
    'command',
    'CommandError',
    'register_system_command',
    'register_gameplay_command'
]

__gameplay_commands = dict()
__system_commands = dict()


class CommandError(RuntimeError):
    pass


def command(cmd, requestor, depth=0):
    assert(len(cmd) > 0)

    logging.trace('Dispatch command "{}" for {}', cmd, requestor.name)

    if depth > 4:
        raise CommandError('Recursive aliases detected.')

    aliases = getattr(requestor, 'aliases', None)

    firstword = cmd.split(' ')[0] # TODO handle \t

    if aliases:
        try:
            alias = aliases[firstword]
        except KeyError:
            pass
        else:
            command(aliases[firstword], requestor, depth + 1)
            return

    if firstword[0] == '@':
        try:
            syscommand = __system_commands[firstword]
        except KeyError:
            pass
        else:
            syscommand(cmd, requestor)
            return
    else:
        try:
            gamecommand = __gameplay_commands[firstword]
        except KeyError:
            pass
        else:
            gamecommand(cmd, requestor)
            return

    logging.trace('Command not found!')
    logging.trace('  __system_commands = {}    __gameplay_commands = {}',
                  pprint.pformat(__system_commands.keys()),
                  pprint.pformat(__gameplay_commands.keys()))

    raise CommandError('Unknown command!')


def register_system_command(name, cmd):
    assert(cmd)

    if len(name) == 0 or name[0] != '@':
       raise RuntimeError("Invalid cmd name '%s' at command registration" % name) 

    global __system_commands

    __system_commands[name] = cmd


def register_gameplay_command(name, cmd):
    assert(cmd)

    if len(name) == 0 or name[0] == '@':
       raise RuntimeError("Invalid cmd name '%s' at command registration" % name) 

    global __system_commands

    __gameplay_commands[name] = cmd

# import plugins
from .commands import *

