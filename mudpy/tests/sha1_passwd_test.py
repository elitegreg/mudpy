import unittest

from utils.sha1_passwd import *

PASSWD = 'this_is_a_test_passwd12345'

class PasswordTestCase(unittest.TestCase):
  def test_sha1_passwd(self):
    sh = passwd(PASSWD)
    self.assertTrue(compare(sh, PASSWD))
    self.assertFalse(compare(sh, 'not the real password'))
    self.assertFalse(compare('', ''))
    

if __name__ == '__main__':
  unittest.main()
