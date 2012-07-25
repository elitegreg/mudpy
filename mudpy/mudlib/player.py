from .object import Object

from mudpy.driver import logging

from mudpy.driver.check_color import *
from mudpy.driver.database import *
from mudpy.utils import passwd_tool
from mudpy.utils.prompt import prompt

from greenlet import getcurrent

from tyderium.telnet import *

from datetime import datetime
import yaml


class Player(Object, yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Player'

    @staticmethod
    def new_character(ts):
        while True:
            name = prompt(ts, 'New Character Name: ').lower()

            if ' ' in name:
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
                pass1 = prompt(ts, 'Password: ')
                ts.sendtext('\n')
                pass2 = prompt(ts, 'Password (verify): ')
                ts.sendtext('\n')

            if pass1 == pass2:
                break

            ts.sendtext('Passwords do not match!\n')

        email = prompt(ts, 'EMail Address: ')

        logging.info('Creating new player: {}', name)

        player = ObjectCache().get(oid, Player, name, pass1, email)
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
                pass1 = prompt(ts, 'Password: ')

            if player.check_password(pass1):
                getcurrent().hub.spawn(player.telnet_attach, ts)
                return True

            ts.sendtext('Incorrect password!\n')

        ts.sendtext('Goodbye!\n')
  
    def __init__(self, oid, name, password, email):
        super().__init__(oid)
        self.__name = name
        self.__display_name = name.capitalize()
        self.__password = passwd_tool.passwd(password)
        self.__email = email
        self.__last_ip = None
        self.__last_time = None
        self.__color = False
        self.__window_size = (80, 25)

    def __getstate__(self):
        d = super().__getstate__()
        d.pop('_Player__color')
        d.pop('_Player__window_size')
        return d

    def check_password(self, password):
        return passwd_tool.compare(self.__password, password)

    @property
    def email(self):
        return self.__email

    @property
    def name(self):
        return self.__name

    @property
    def display_name(self):
        return self.__display_name

    def setup(self):
        super().setup()

    def telnet_attach(self, ts):
        self.__color = has_color(ts.options.term)
        self.__window_size = ts.options.window_size

        ts.sendtext('Color {}\n'.format('Enabled' if self.__color else 'Disabled'))
        ts.sendtext('Window Size: {} {}\n'.format(*self.__window_size))

        if self.__last_ip:
            ts.sendtext('Last login from {} on {}\n'.format(
                self.__last_ip, self.__last_time))

        self.__last_ip = ts.socket.getpeername()[0]
        self.__last_time = datetime.now().ctime()

        while True:
            cmd = prompt(ts, '> ').rstrip()
  
            if cmd == '':
                continue
            elif cmd.lower() == 'hi':
                ts.sendtext('Hello!\n')
            elif cmd.lower() == 'quit':
                self.save()
                ts.sendtext('Goodbye!\n')
                ts.socket.close()
                return
            else:
                ts.sendtext('Unknown command!\n')


def new_connection(conn, addr):
    try:
        logging.info('New connection from: {}', addr[0])

        ts = TelnetStream(conn)

        if config.telnet.terminal_type_support:
            ts.request_terminal_type()
        if config.telnet.utf8_support:
            ts.enable_binary_mode()
        if config.telnet.window_size_support:
            ts.request_window_size()

        while True:
            name = prompt(ts, 'Character Name (or "new"): ').lower()

            if name == 'new':
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


