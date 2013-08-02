from .object import Object

from .command import command, CommandError

from mudpy import logging

from mudpy.check_color import *
from mudpy.database import *
from mudpy.gameproperty import add_gameproperty
from mudpy.utils import ansi
from mudpy.utils import passwd_tool

from greenlet import getcurrent, GreenletExit

from tyderium.telnet import *

from datetime import datetime

import socket
import textwrap
import yaml


class Player(Object, yaml.YAMLObject):
    __slots__ = ('__telnet_stream',)

    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Player'

    @staticmethod
    def new_character(ts):
        while True:
            name = ts.prompt('New Character Name: ').lower()

            if ' ' in name or len(name) == 0:
                ts.sendtext('Invalid Name.\n')
                continue

            try:
                oid = Object_ID('/players/%s/player' % name)
                player = ObjectCache().get(oid)
                ts.sendtext('That name is already in use.\n')
            except DoesNotExist:
                break

        while True:
            with NoEcho(ts):
                pass1 = ts.prompt('Password: ')
                ts.sendtext('\n')
                pass2 = ts.prompt('Password (verify): ')
                ts.sendtext('\n')

            if pass1 == pass2:
                break

            ts.sendtext('Passwords do not match!\n')

        email = ts.prompt('EMail Address: ')

        logging.info('Creating new player: {}', name)

        d = {
            'name' : name,
            'password' : passwd_tool.passwd(pass1),
            'email' : email
            }

        player = ObjectCache().get(oid, Player, d)
        player.save()
        getcurrent().hub.spawn(player.telnet_attach, ts)


    @staticmethod
    def login(ts, name):
        try:
            player = ObjectCache().get(Object_ID('/players/%s/player' % name))
        except DoesNotExist:
            ts.sendtext('That Character Does Not Exist!\n')
            return False

        for i in range(0, 2):
            with NoEcho(ts):
                pass1 = ts.prompt('Password: ')

            if player.check_password(pass1):
                getcurrent().hub.spawn(player.telnet_attach, ts)
                return True

            ts.sendtext('Incorrect password!\n')

        ts.sendtext('Goodbye!\n')

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

    def telnet_attach(self, ts):
        try:
            self.__telnet_stream = ts

            if (self.color == 'auto' and has_color(ts.options.term)) or \
                    self.color == 'on':
                self.__telnet_stream.colormap = ansi.ANSI_MAP

            if self.last_ip:
                ts.write('${BRIGHT_WHITE}Last login from %s on %s${DEFAULT}' % (
                    self.last_ip, self.last_time))

            self.last_ip = ts.socket.getpeername()[0]
            self.last_time = datetime.now().ctime()

            command('look', self)

            while True:
                cmd = ts.prompt('> ', quit_on_eot=True).strip().lower()
      
                if cmd == '':
                    continue
                else:
                    try:
                        command(cmd, self)
                    except CommandError as e:
                        ts.write(str(e))
        except (ConnectionClosed, socket.error):
            self.__telnet_stream = None


def new_connection(conn, addr):
    try:
        logging.info('New connection from: {}', addr[0])

        ts = PlayerTelnetStream(conn)

        while True:
            name = ts.prompt('Character Name (or "new"): ').lower()

            if name == '':
                continue
            elif name == 'new':
                Player.new_character(ts)
                return
            else:
                if Player.login(ts, name):
                    return
    except LineTooLong:
        logging.info('Connection closed due to buffer overrun: {}',
                     addr[0])
        conn.close()
    except ConnectionClosed:
        logging.info('Connection closed: {}', addr[0])
        conn.close()


class PlayerTelnetStream(TelnetStream):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if config.telnet.terminal_type_support:
            self.request_terminal_type()
        if config.telnet.utf8_support:
            self.enable_binary_mode()
        if config.telnet.window_size_support:
            self.request_window_size()

        self.colormap = ansi.DEFAULT_MAP

    def prompt(self, msg, quit_on_eot=False):
        while True:
            try:
                self.sendtext(msg)
                return self.readline().rstrip()
            except Interrupt:
                self.sendtext('\n')
            except EOTRequested:
                if quit_on_eot:
                    return 'quit'
                self.close()
                raise GreenletExit

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

