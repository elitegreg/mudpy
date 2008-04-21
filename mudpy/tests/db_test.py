import os
import shutil
import unittest

from driver.database import *


class TestType(object):
  def __init__(self, oid):
    self.oid = oid
    self.data = dict()

  def setup(self):
    global SETUP
    SETUP += 1

  def save(self):
    global SAVES
    SAVES += 1
    return self.data

  def restore(self, data):
    global RESTORES
    RESTORES += 1
    self.data.update(data)


class DBTestCase(unittest.TestCase):
  DIR = '_DBTestCase_.tmp'

  TESTDATA = {'a':1, 'b':2, 'c':3}

  def setUp(self):
    try:
      os.mkdir(DBTestCase.DIR)
    except:
      pass

    DB.DBDIR = DBTestCase.DIR

    # clear ObjectCache
    ObjectCache().clear()

    global RESTORES
    global SAVES
    global SETUP
    RESTORES = 0
    SAVES = 0
    SETUP = 0

  def tearDown(self):
    shutil.rmtree(DBTestCase.DIR)

  def test_db(self):
    # set the tests object id:
    oid = 'test.db:/testpath/testobj'

    # initialize variables
    cache = ObjectCache()
    db = DB()

    # The DB is empty. Try loading the object, expect KeyError
    self.assertRaises(KeyError, cache.get_obj, oid)

    # Now create the object
    obj = cache.get_obj(oid, create=TestType)
    obj.data.update(DBTestCase.TESTDATA)
    
    # save it
    DB().save_obj(obj)

    # validate save and restore count
    self.assertEquals(RESTORES, 0)
    self.assertEquals(SAVES, 1)
    self.assertEquals(SETUP, 1)

    # validate the DB file is on disk
    self.assertTrue(os.path.exists(os.path.join(DBTestCase.DIR,
      'test.db')))

    # ask the object cache for the object multiple times. Expect to get
    # the same object back (because it is cached)
    obj2 = cache.get_obj(oid)
    obj3 = cache.get_obj(oid, create=TestType)

    # validate is the same object
    self.assertTrue(obj is obj2)
    self.assertTrue(obj is obj3)

    # validate save and restore count
    self.assertEquals(RESTORES, 0)
    self.assertEquals(SAVES, 1)
    self.assertEquals(SETUP, 1)

    # delete the last 2 references
    del obj2, obj3

    # clear the cache
    cache.destroy(oid)

    # load the object. should load from disk because cache is clear.
    obj2 = cache.get_obj(oid)

    # validate correct data
    self.assertEquals(obj2.data, DBTestCase.TESTDATA)

    # validate save and restore count
    self.assertEquals(RESTORES, 1)
    self.assertEquals(SAVES, 1)
    self.assertEquals(SETUP, 1)

    # make sure obj and obj2 reference different objects
    self.assertFalse(obj is obj2)

    # delete references
    del obj, obj2

    # clear the cache
    cache.destroy(oid)

    # base obj
    obj = cache.get_obj(oid)

    # clone object
    self.assertRaises(KeyError, cache.get_obj, oid + '#')
    clone = cache.get_obj(oid + '#', create=TestType)

    # make sure clone id number is set
    int(clone.oid[len(oid)+1:])

    # make another clone
    clone2 = cache.get_obj(oid + '#', create=TestType)

    # make sure they aren't the same object, and not same clone
    self.assertFalse(clone is clone2)
    self.assertNotEqual(clone.oid, clone2.oid)

    # make sure neither is the base object, but verify the contents
    self.assertFalse(clone is obj)
    self.assertFalse(clone2 is obj)
    self.assertEquals(clone.data, obj.data)
    self.assertEquals(clone2.data, obj.data)

    # load the original clone from the object cache and make sure its
    # the same object!
    clone3 = cache.get_obj(clone.oid)
    self.assertTrue(clone3 is clone)

    # try to save a clone, should fail
    self.assertRaises(RuntimeError, db.save_obj, clone)

    # delete references
    del obj, clone, clone2, clone3

    # delete the object from the database
    # edlete an invalid object from the database
    db.delete_id(oid)
    db.delete_id(oid + '_foo')

    # try and load deleted object, expect KeyError
    self.assertRaises(KeyError, db.load_obj, oid)

    # make sure loading a uncached clone fails
    self.assertRaises(KeyError, cache.get_obj, oid + '#98765')

  def test_oid(self):
    self.assertRaises(RuntimeError, Object_ID, 'test.db-obj-/test')

    oid1 = 'test.db:/testpath/testobj'
    oid_obj = Object_ID(oid1)
    self.assertEquals(str(oid_obj), oid1)
    self.assertEquals(oid_obj.dbname, 'test.db')
    self.assertEquals(oid_obj.id, '/testpath/testobj')
    self.assertFalse(oid_obj.is_clone)
    self.assertTrue(oid_obj.clone_id is None)
    self.assertRaises(RuntimeError, oid_obj.add_clone_id, 12345)
    oid_obj.drop_clone()
    self.assertEquals(str(oid_obj), oid1)

    oid2 = oid1 + '#12345'
    oid_obj = Object_ID(oid2)
    self.assertEquals(str(oid_obj), oid2)
    self.assertEquals(oid_obj.dbname, 'test.db')
    self.assertEquals(oid_obj.id, '/testpath/testobj')
    self.assertTrue(oid_obj.is_clone)
    self.assertEquals(oid_obj.clone_id, '12345')
    oid_obj.add_clone_id(99)
    self.assertEquals(oid_obj.clone_id, '99')
    oid_obj.drop_clone()
    self.assertFalse(oid_obj.is_clone)
    self.assertTrue(oid_obj.clone_id is None)
    self.assertEquals(str(oid_obj), oid1)

if __name__ == '__main__':
  unittest.main()

