import Auth
import database
import logging
import logging.config
import pprint
import reactor
import signals
import sqlalchemy
import TelnetServer

# db objects
import mudlib.player

logger = logging.getLogger('Driver')


def create_metadata():
  db = database.Database()
  metadata = sqlalchemy.MetaData()
  mudlib.player.register_table(metadata)
  metadata.create_all(db)


def user_authorized(conn, user):
  logger.info('%s connected and authorized', user)

def user_unauthorized(conn, user):
  logger.info('%s connected and unauthorized', user)

logging.config.fileConfig('etc/logger.cfg')

db = database.Database()
db.open_db('sqlite:///mudlib.db')
session = database.Session()
session.open_session(db)
create_metadata()

auth_daemon = Auth.AuthDaemon()

def handle_new_connection(conn):
  auth_daemon.auth(conn)

def new_user(conn, properties):
  logger.info('New user: %s', properties.get('name'))
  logger.info('New user properties: %s', pprint.pformat(properties))
  player = mudlib.player.Player(**properties)
  cache = database.ObjectCache()
  cache.save(player)
  player = cache.lookup(mudlib.player.Player, player.id)

  
server = TelnetServer.TelnetServer(port=12345)
server.connect_handler.connect(handle_new_connection)

signals.user_authorized_signal.connect(user_authorized)
signals.user_unauthorized_signal.connect(user_unauthorized)
signals.new_user_signal.connect(new_user)

reactor.reactor.start_reactor()
reactor.reactor.close()

