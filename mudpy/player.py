from .object import Object

from .command import command, CommandError

from mudpy import logging

from mudpy.check_color import *
from mudpy.database import *
from mudpy.gameproperty import add_gameproperty
from mudpy.telnet import *
from mudpy.utils import ansi
from mudpy.utils import passwd_tool

from datetime import datetime

import asyncio
import socket
import textwrap
import yaml


class Player(Object, yaml.YAMLObject):
    __slots__ = ('__telnet_stream',)

    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Player'

    @staticmethod
    async def login(proto):
        addr = proto.transport.get_extra_info('peername')[0]

        logging.info('New connection from: {}', addr)

        try:
            for i in range(0, config.max_login_attempts):
                name = (await proto.prompt('Character Name (or "new"): ')).lower()

                if name == 'new':
                    player = await Player.new_character(proto)
                    break
                elif name != '':
                    try:
                        player = ObjectCache().get(Object_ID('/players/{}/player'.format(name)))
                    except DoesNotExist:
                        proto.sendtext('That Character Does Not Exist!\n')
                        continue

                    for i in range(0, 2):
                        with NoEcho(proto):
                            pass1 = await proto.prompt('Password: ')

                        if not player.check_password(pass1):
                            proto.sendtext('Incorrect password!\n')
                        else:
                            break
                    else:
                        player = None

                    break
            else:
                player = None

            if player:
                await player.telnet_attach(proto)

            proto.sendtext('Goodbye!\n')
            proto.close()
            raise ConnectionClosed()

        except LineTooLong:
            logging.info('Connection closed due to buffer overrun: {}', addr)
        except ConnectionClosed:
            logging.info('Connection closed: {}', addr)
        except SenderTooFast:
            logging.info('Connection closed due to fast sender (queue full): {}', addr)

    @staticmethod
    async def new_character(proto):
        while True:
            name = (await proto.prompt('New Character Name: ')).lower()

            if ' ' in name or len(name) == 0:
                proto.sendtext('Invalid Name.\n')
                continue

            try:
                oid = Object_ID('/players/{}/player'.format(name))
                player = ObjectCache().get(oid)
                proto.sendtext('That name is already in use.\n')
            except DoesNotExist:
                break

        while True:
            with NoEcho(proto):
                pass1 = await proto.prompt('Password: ')
                proto.sendtext('\n')
                pass2 = await proto.prompt('Password (verify): ')
                proto.sendtext('\n')

            if pass1 == pass2:
                break

            proto.sendtext('Passwords do not match!\n')

        email = await proto.prompt('EMail Address: ')

        logging.info('Creating new player: {}', name)

        d = {
            'name' : name,
            'password' : passwd_tool.passwd(pass1),
            'email' : email
            }

        player = ObjectCache().get(oid, Player, d)
        player.save()
        return player

    def __setstate__(self, newstate):
        super().__setstate__(newstate)
        if not self.aliases:
            self.aliases = config.player.default_aliases.copy()
        if not self.display_name:
            self.display_name = self.name.capitalize()
        if not self.environment:
            self.environment = ObjectCache().get(Object_ID('/rooms/sample1'))

    def check_password(self, password):
        return passwd_tool.compare(self.password, password)

    def write(self, msg):
        self.__telnet_stream.write(msg)

    def disconnect(self):
        self.__telnet_stream.close()

    async def telnet_attach(self, proto):
        try:
            self.__telnet_stream = proto

            if (self.color == 'auto' and has_color(proto.options.term)) or \
                    self.color == 'on':
                self.__telnet_stream.colormap = ansi.ANSI_MAP

            if self.last_ip:
                proto.write('${{BRIGHT_WHITE}}Last login from {} on {}${{DEFAULT}}'.format(
                    self.last_ip, self.last_time))

            self.last_ip = proto.transport.get_extra_info('peername')[0]
            self.last_time = datetime.now().ctime()

            command('look', self)

            while True:
                cmd = (await proto.prompt('> ', quit_on_eot=True)).strip().lower()
      
                if cmd == '':
                    continue
                else:
                    try:
                        command(cmd, self)
                    except CommandError as e:
                        proto.write(str(e))
        except (ConnectionClosed, socket.error):
            self.__telnet_stream = None


class PlayerTelnetProtocol(TelnetProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colormap = ansi.DEFAULT_MAP

    def connection_made(self, transport):
        super().connection_made(transport)

        if config.telnet.terminal_type_support:
            self.request_terminal_type()
        if config.telnet.utf8_support:
            self.enable_binary_mode()
        if config.telnet.window_size_support:
            self.request_window_size()

        asyncio.get_event_loop().create_task(Player.login(self))

    async def prompt(self, msg, quit_on_eot=False):
        while True:
            try:
                self.sendtext(msg)
                data = (await self.readline()).rstrip()
                if self.echo is False:
                    self.sendtext('\n')
                return data
            except Interrupt:
                self.sendtext('\n')
            except EOTRequested:
                if quit_on_eot:
                    return 'quit'
                self.close()
                raise asyncio.CancelledError()

    def write(self, msg):
        # textwrap ignoring ESC sequences
        msg = ansi.map_string(msg, self.colormap) 
        msg = textwrap.fill(msg, width=self.options.window_size[0])
        msg += '\n'
        self.sendtext(msg)


add_gameproperty(Player, 'name', readonly=True)
add_gameproperty(Player, 'display_name')
add_gameproperty(Player, 'password', readonly=True)
add_gameproperty(Player, 'email')
add_gameproperty(Player, 'last_ip')
add_gameproperty(Player, 'last_time')
add_gameproperty(Player, 'color', default='auto')
add_gameproperty(Player, 'aliases')

