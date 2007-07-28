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

  return "%s%s" % (salt, sha.new(salt + password).hexdigest())


def compare(salted_hash, password):
  (salt, passwd_hash) = (salted_hash[0:4], salted_hash[4:])
  return salted_hash == passwd(password, salt)

