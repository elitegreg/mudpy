import eventlet

import optparse
import os
import socket
import ssl


def listen(addr, port, socktype = socket.SOCK_STREAM, proto = socket.IPPROTO_TCP):
    (family, sockytype, proto, canonname, sockaddr) = \
            socket.getaddrinfo(addr, port, 0, socktype, proto)[0]
    return eventlet.listen(sockaddr, family)


def serve(sock, *a, **kw):
    while True:
        try:
            return eventlet.serve(sock, *a, **kw)
        except ssl.SSLEOFError:
            pass


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
        with logging.initialize(getattr(config.log, 'log_file', None)):
            telnet_socket = listen(config.telnet.bind_address, config.telnet.bind_port)
            eventlet.spawn(serve, telnet_socket, mudlib.player.new_connection)

            ssl_bind_address = getattr(config.telnet, 'ssl_bind_address', '')
            ssl_bind_port = getattr(config.telnet, 'ssl_bind_port', None)
            ssl_cert = getattr(config.telnet, 'ssl_cert', None)

            if ssl_bind_address and ssl_bind_port and ssl_cert:
                ssl_telnet_socket = eventlet.wrap_ssl(
                    listen(ssl_bind_address, ssl_bind_port), certfile=ssl_cert)
                eventlet.spawn(serve, ssl_telnet_socket, mudlib.player.new_connection)

            while True:
                eventlet.sleep(1)
                # TODO heartbeat here?

    except KeyboardInterrupt:
        logging.fatal('MUD Shutdown due to keyboard request')
    except:
        logging.exception("MUD Shutdown due to exception!")

