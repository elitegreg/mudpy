import logging
import os
import utils.sha1_passwd

logger = logging.getLogger('Database')


class Database(object):
  def __init__(self, db_uri):
    pass

  def auth_user(self, user, password):
    return True

  def create_object(self, object_type, object_id):
    pass

  def load_object(self, object_type, object_id):
    pass

  def create_user(self, username, password, email, ip, login_time):
    pass

  def load_user(self, username):
    pass

  def update_user(self, username, password, email, ip, login_time):
    pass

  def update_properties(self, id, properties):
    pass

