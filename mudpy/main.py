import contextlib
import optparse
import os
import socket
import ssl


def create_server(factory, addr, port, ssl=None):
    (family, sockytype, proto, canonname, sockaddr) = \
            socket.getaddrinfo(addr, port, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP)[0]
    return asyncio.get_event_loop().create_server(factory, addr, port, family=family, ssl=ssl)


def serve(sock, *a, **kw):
    while True:
        try:
            return eventlet.serve(sock, *a, **kw)
        except ssl.SSLEOFError:
            pass

def sslcontext(certfile):
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.load_cert_chain(certfile)
    return ctx

class DummyServer:
    def close():
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
    logging.monkey_patch()

    from mudpy import mudlib
    from mudpy import player

    import asyncio

    eventloop = asyncio.get_event_loop()

    try:
        with logging.initialize(getattr(config.log, 'log_file', None)):
            server = eventloop.run_until_complete(
                create_server(player.PlayerTelnetProtocol,
                              config.telnet.bind_address,
                              config.telnet.bind_port))
            with contextlib.closing(server):
                tasks = [server.wait_closed()]
                ssl_bind_address = getattr(config.telnet, 'ssl_bind_address', '')
                ssl_bind_port = getattr(config.telnet, 'ssl_bind_port', None)
                ssl_cert = getattr(config.telnet, 'ssl_cert', None)

                if ssl_bind_address and ssl_bind_port and ssl_cert:
                    ssl_server = eventloop.run_until_complete(
                        create_server(player.PlayerTelnetProtocol,
                                      ssl_bind_address,
                                      ssl_bind_port,
                                      sslcontext(ssl_cert)))
                    tasks.append(ssl_server.wait_closed())
                else:
                    ssl_server = DummyServer()

                with contextlib.closing(ssl_server):
                    eventloop.run_until_complete(asyncio.wait(tasks))

    except KeyboardInterrupt:
        logging.fatal('MUD Shutdown due to keyboard request')
    except:
        logging.exception("MUD Shutdown due to exception!")

