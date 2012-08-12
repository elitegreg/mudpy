import optparse
import os

from tyderium.hub import Hub
from tyderium.server import Listener
from tyderium.timers import start_timer_service


if __name__ == '__main__':
    parser = optparse.OptionParser('%prog configfile')

    opt, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Expected 1 argument: config file')

    from . import config
    config.load(args[0])

    from . import database
    from . import logging

    from mudpy import mudlib

    try:
        with Hub() as hub:
            start_timer_service(hub)

            hub.spawn(
                Listener(
                    (config.telnet.bind_address, config.telnet.bind_port),
                    mudlib.player.new_connection,
                    pf=config.telnet.address_family).serve)
            hub.switch()
    except KeyboardInterrupt:
        logging.fatal('MUD Shutdown due to keyboard request')
    except:
        logging.exception("MUD Shutdown due to exception!")

