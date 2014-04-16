import unittest

import lockserver_daemon as lockserver


class TheTestCase(unittest.TestCase):

  def setUp(self):
    # Reset the lockserver's global variables between each test.
    lockserver.init_globals()


  def testContentionForSingleUserLock(self):
    # This entire test will use this same lockdict in each request
    locks = {'user':['bob']}
    
    # Start three sessions.
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())

    # Have all three session try to acquire a lock on a single user.
    lockserver.do_acquire_locks(sess[0], locks)
    lockserver.do_acquire_locks(sess[1], locks)
    lockserver.do_acquire_locks(sess[2], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'node': {},
      'user': {'bob': {'locked_by_session': sess[0],
                       'queue': [sess[1], sess[2]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'node': [], 'user': ['bob']},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
    
    # Have the session that holds the lock release it.
    lockserver.do_release_locks(sess[0], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'node': {},
      'user': {'bob': {'locked_by_session': sess[1],
                       'queue': [sess[2]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'node': [], 'user': ['bob']},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
  
    # The session that just released it tries to acquire it again.
    lockserver.do_acquire_locks(sess[0], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'node': {},
      'user': {'bob': {'locked_by_session': sess[1],
                       'queue': [sess[2], sess[0]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False},
      sess[1]: {'heldlocks': {'node': [], 'user': ['bob']},
                'neededlocks': {'node': [], 'user': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'node': [], 'user': []},
                'neededlocks': {'node': [], 'user': ['bob']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])


  def testContentionForSingleNodeLock(self):
    """
    This is the same as testContentionForSingleUserLock but involves contention
    over a single node lock rather than over a single user lock. Both could have
    been done with much less code using a helper method, but that makes the
    dictionaries of expected data much less intuitive to look at and thus
    makes the tests hard to understand. So, just duplicating code, instead. 
    """
    # This entire test will use this same lockdict in each request
    locks = {'node':['123']}
    
    # Start three sessions.
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())

    # Have all three session try to acquire a lock on a single user.
    lockserver.do_acquire_locks(sess[0], locks)
    lockserver.do_acquire_locks(sess[1], locks)
    lockserver.do_acquire_locks(sess[2], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'user': {},
      'node': {'123': {'locked_by_session': sess[0],
                       'queue': [sess[1], sess[2]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': [], 'node': ['123']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False},
      sess[2]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
    
    # Have the session that holds the lock release it.
    lockserver.do_release_locks(sess[0], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'user': {},
      'node': {'123': {'locked_by_session': sess[1],
                       'queue': [sess[2]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'user': [], 'node': ['123']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
  
    # The session that just released it tries to acquire it again.
    lockserver.do_acquire_locks(sess[0], locks)
    
    # The first session should have the lock and the other two sessions should
    # be queued in order for that lock.
    expected_heldlockdict = {
      'user': {},
      'node': {'123': {'locked_by_session': sess[1],
                       'queue': [sess[2], sess[0]]}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False},
      sess[1]: {'heldlocks': {'user': [], 'node': ['123']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False}}
    
    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])

