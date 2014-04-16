

import unittest

import lockserver_daemon as lockserver


class TheTestCase(unittest.TestCase):

  def setUp(self):
    # Reset the lockserver's global variables between each test.
    lockserver.init_globals()


  def testStartSessionCreatesNonemptyStringsForIds(self):
    sess = []
    sess.append(lockserver.do_start_session())
    
    self.assertNotEqual(sess[0], '')
    self.assertTrue(isinstance(sess[0], str))


  def testStartSessionCreatesUniqueIds(self):
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    
    self.assertNotEqual(sess[0], sess[1])
    self.assertNotEqual(sess[1], sess[2])
    
    
  def testEndSession(self):
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    
    expected_heldlockdict = {
      'node': {},
      'user': {}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
    
    # End the first session.
    lockserver.do_end_session(sess[0])
    
    expected_heldlockdict = {
      'node': {},
      'user': {}}
    expected_sessiondict = {
      sess[1]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
    
    # Make sure we aren't allowed to use the session we just ended in a lock request.
    locks = {'user':['bob']}
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    # Make sure we aren't allowed to end the same session again.
    func = lockserver.do_end_session
    args = (sess[0],)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    # Make sure the sessions we didn't end still work (the second session
    # will acquire the lock, the third session will be queued for it).
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[1], locks)
    lockserver.do_acquire_locks(sess[2], locks)
    
    expected_heldlockdict = {
      'node': {},
      'user': {'bob': {'locked_by_session': sess[1],
                       'queue': [sess[2]]}}}
    expected_sessiondict = {
      sess[1]: {'heldlocks': {'node': [], 'user': ['bob']},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])


  def testEndSessionFailsWhenSessionNotEmpty(self):
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    
    # Have the first session acquire a lock.
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[0], locks)
    
    # Make sure we can't end the session while the session holds locks.
    func = lockserver.do_end_session
    args = (sess[0],)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
  
    # Have the second session be queued for the same lock.
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[1], locks)
    
    # Make sure we can't end the session while the session has pending
    # lock acquisition requests.
    func = lockserver.do_end_session
    args = (sess[0],)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)


  def testNonexistentSessionId(self):
    
    sess = []
    sess.append('1234')
    
    # Try to acquire locks with the non-existent session.
    locks = {'user':['bob']}
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
    
    # Try to release locks with the non-existent session.
    locks = {'user':['bob']}
    func = lockserver.do_acquire_locks
    args = (sess[0], locks)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
  
    # Try to end the non-existent session.
    func = lockserver.do_end_session
    args = (sess[0],)
    self.assertRaises(lockserver.LockserverInvalidRequestError, func, *args)
  
