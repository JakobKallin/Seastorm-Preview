import unittest

import lockserver_daemon as lockserver


class TheTestCase(unittest.TestCase):

  def setUp(self):
    # Reset the lockserver's global variables between each test.
    lockserver.init_globals()


  def testLockdictWithMultipleLockTypes(self):
    
    sess = []
    sess.append(lockserver.do_start_session())
    
    # It is not allowed to make a single request for multiple types of locks.
    locks = {'user':['bob'], 'node':['123']}
    
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)


  def testRequestForTypeOfLockAlreadyHeld(self):
    
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    
    # First session gets a lock on user 'bob'
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[0], locks)
    
    # First session then tries to get another user lock, which it shouldn't be
    # allowed to do while it already holds a user lock.
    locks = {'user':['alice']}
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)

    # Second session gets a lock on node '123'.
    locks = {'node':['123']}
    lockserver.do_acquire_locks(sess[1], locks)
    
    # Second session then tries to get another node lock, which it shouldn't be
    # allowed to do while it already holds a node lock.
    locks = {'node':['123']}
    
    func = lockserver.do_acquire_locks
    args = (sess[1], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)

    
  def testRequestForUserLockWhileHoldingNodeLock(self):
    
    sess = []
    sess.append(lockserver.do_start_session())
    
    # First session gets a lock on node '123'
    locks = {'node':['123']}
    lockserver.do_acquire_locks(sess[0], locks)
    
    # First session then tries to get a user lock, which it shouldn't be
    # allowed to do while it already holds a node lock.
    locks = {'user':['bob']}
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)

