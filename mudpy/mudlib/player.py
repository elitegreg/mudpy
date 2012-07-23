from .object import Object

from mudpy.driver import logging

from mudpy.driver.check_color import *
from mudpy.driver.database import *
from mudpy.utils.passwd_tool import *
from mudpy.utils.prompt import prompt

from greenlet import getcurrent

from tyderium.telnet import *

import yaml


class Player(Object, yaml.YAMLObject):
  yaml_loader = yaml.SafeLoader
  yaml_tag = '!Player'

  def __init__(self, oid, name, password, email):
    super().__init__(oid)
    self.__name = name
    self.__password = passwd(password)
    self.__email = email

  @property
  def email(self):
    return self.__email

  @property
  def name(self):
    return self.__name

  def setup(self):
    super().setup()

  def telnet_attach(self, ts):
    while True:
      cmd = prompt(ts, '> ')

      if cmd.lower() == 'hi':
        ts.sendtext('Hello!\n')
      elif cmd.lower() == 'quit':
        ts.sendtext('Goodbye!\n')
        ts.socket.close()
        return
      else:
        ts.sendtext('Unknown command!')


def validate_player_name(name):
  return ' ' not in name


def new_character(ts, color):
    while True:
        name = prompt(ts, 'New Character Name: ')

        if not validate_player_name(name):
            ts.sendtext('Invalid Name.\n')
            continue

        try:
            oid = Object_ID('/players/%s' % name)
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
    DB().save_obj(player)
    getcurrent().hub.spawn(player.telnet_attach, ts)


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

        opts = ts.readoptions(config.telnet.readoptions_sleep_time)

        color = has_color(opts.term)
        logging.debug('Connection:{},{},color={}', ts, opts, color)

        name = prompt(ts, 'Character Name (or "new"): ')

        if name.lower() == 'new':
            new_character(ts, color)
        else:
            with NoEcho(ts):
                password = prompt(ts, 'Password: ')
                ts.sendtext('\n')
    except LineTooLong:
        logging.info('Connection closed due to buffer overrun: {}',
                     addr[0])
        conn.close()
    except ConnectionClosed:
        logging.info('Connection closed: {}', addr[0])
        conn.close()


