import unittest

import lockserver_daemon as lockserver


class TheTestCase(unittest.TestCase):
  
  def setUp(self):
    # Reset the lockserver's global variables between each test.
    lockserver.init_globals()
    
    
  def testSessionIdThatIsNotAString(self):
    
    session_id = 1
    
    func = lockserver._assert_valid_lockdict
    args = (session_id,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    session_id = []
    
    func = lockserver._assert_valid_lockdict
    args = (session_id,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    session_id = None
    
    func = lockserver._assert_valid_lockdict
    args = (session_id,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    
  def testSessionIdThatIsAnEmptyString(self):
    
    session_id = ''
    
    func = lockserver._assert_valid_lockdict
    args = (session_id,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    
  def testLockdictWithNoLocks(self):
    
    locks = {}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    

  def testLockdictWithUnknownLockType(self):
    
    # 'xxx' is not a valid type of lock.
    locks = {'xxx':['bob']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    
  def testLockdictWithListOfNamesThatIsNotAList(self):
    
    locks = {'user':{}}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    locks = {'user':None}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    
  def testLockdictWithEmptyListOfLockNames(self):
    
    locks = {'user':[]}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    locks = {'node':[]}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)


  def testLockdictWithEmptyStringInLockNames(self):
    
    locks = {'user':['bob', '']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    locks = {'node':['', '123']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)


  def testLockdictWithLockTypesThatAreNotStrings(self):
    
    locks = {123:['bob']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    

  def testLockdictWithLockNamesThatAreNotStrings(self):
    
    locks = {'user':['bob', None]}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    locks = {'node':[123, '123']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    locks = {'node':[[], '123']}
    
    func = lockserver._assert_valid_lockdict
    args = (locks,)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    
