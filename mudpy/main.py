import gevent
import gevent.server

import optparse
import os


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
        telnet_server = gevent.server.StreamServer(
            (config.telnet.bind_address, config.telnet.bind_port),
            mudlib.player.new_connection)
        telnet_server.start()

        ssl_bind_address = getattr(config.telnet, 'ssl_bind_address', None)
        ssl_bind_port = getattr(config.telnet, 'ssl_bind_port', None)
        ssl_cert = getattr(config.telnet, 'ssl_cert', None)

        if ssl_bind_address and ssl_bind_port and ssl_cert:
            ssl_telnet_server = gevent.server.StreamServer(
                (config.telnet.bind_address, config.telnet.ssl_bind_port),
                mudlib.player.new_connection,
                certfile=ssl_cert)
            ssl_telnet_server.start()

        while True:
            gevent.sleep(1)
            # TODO heartbeat here?

    except KeyboardInterrupt:
        logging.fatal('MUD Shutdown due to keyboard request')
    except:
        logging.exception("MUD Shutdown due to exception!")

