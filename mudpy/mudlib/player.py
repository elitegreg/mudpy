import body
from utils.sha1_passwd import *

class Player(body.Body):
  def __init__(self):
    super(Player, self).__init__()

  def check_password(self, password):
    return compare(self.password, password)

  @property
  def email(self):
    return self.props.get('name')

  @property
  def name(self):
    return self.props.get('name')

  def new_player(self, name, password, email):
    self.props['name'] = name
    self.props['password'] = passwd(password)
    self.props['email'] = email
    self.props.setdefault('nouns', set()).add(name.lower())

  @property
  def password(self):
    return self.props.get('password')

  def quit(self):
    raise NotImplementedError

  def save(self):
    raise NotImplementedError

  def reset(self):
    super(Player, self).reset()

  def restore(self, propdict):
    raise NotImplementedError

  def setup(self):
    super(Player, self).setup()
