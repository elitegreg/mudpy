import hashlib
import random
import string


hash_algo = hashlib.sha1


def passwd(password, salt=None):
  if salt is None:
    salt = ''
    for c in random.sample(string.printable, 4):
      salt = salt + c

  return "%s%s" % (salt, hash_algo(salt + password).hexdigest())


def compare(salted_hash, password):
  (salt, passwd_hash) = (salted_hash[0:4], salted_hash[4:])
  return salted_hash == passwd(password, salt)

