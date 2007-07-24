import logger_config
import logging
import random
import sha
import string


def passwd(password, salt=None):
  if salt is None:
    salt = ''
    for c in random.sample(string.printable, 4):
      salt = salt + c

  return "%s:%s" % (salt, sha.new(salt + password).hexdigest())


def compare(salted_hash, password):
  try:
    (salt, passwd_hash) = salted_hash.split(':', 1)
  except:
    logging.getLogger().warning("sha1_passwd.compare(): salted_hash" +
        " doesn't contain a salt value")
    return False

  return salted_hash == passwd(password, salt)

