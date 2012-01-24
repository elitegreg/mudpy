from mudpy.driver.check_color import has_color

import logging
import optparse
import os
import socket

from khakilet.hub import Hub
from khakilet.server import Listener
from khakilet.telnet import *


def prompt(ts, msg):
    while True:
        try:
            ts.sendtext(msg)
            return ts.readline().rstrip()
        except Interrupt:
            ts.sendtext('\n')
            pass


def new_connection(conn, addr):
    try:
        logging.info('New connection from: %s', addr[0])

        ts = TelnetStream(conn)

        if config.telnet.terminal_type_support:
            ts.request_terminal_type()
        if config.telnet.utf8_support:
            ts.enable_binary_mode()
        if config.telnet.window_size_support:
            ts.request_window_size()

        opts = ts.readoptions(config.telnet.readoptions_sleep_time)

        color = has_color(opts.term)
        logging.debug('...%s,color=%s', opts, color)

        name = prompt(ts, 'Character Name (or "new"): ')

        if name.lower() == 'new':
            logging.debug('Creating new character...')
            new_character(ts, color)
        else:
            with NoEcho(ts):
                password = prompt('Password: ')
                ts.sendtext('\n')
    except LineTooLong:
        logging.info('Connection closed due to buffer overrun: %s',
                     ts.socket.getpeername()[0])
        conn.close()
    except ConnectionClosed:
        logging.info('Connection closed: %s', ts.socket.getpeername()[0])
        conn.close()


if __name__ == '__main__':
    parser = optparse.OptionParser('%prog configfile')

    opt, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Expected 1 argument: config file')

    os.putenv('MUDPY_CONFIG_FILE', args[0])

    try:
        from mudpy.driver import config

        with Hub() as hub:
            hub.spawn(
                Listener(
                    (config.network.bind_address, config.network.bind_port),
                    new_connection,
                    pf=config.network.address_family).serve)
            hub.switch()
    except:
        logging.exception("MUD Shutdown due to exception!")

