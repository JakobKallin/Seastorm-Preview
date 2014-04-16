import unittest

import lockserver_daemon as lockserver


class TheTestCase(unittest.TestCase):

  def setUp(self):
    # Reset the lockserver's global variables between each test.
    lockserver.init_globals()


  def testUserAndNodeLockContention_one(self):
    # Start three sessions.
    sess = []
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())
    sess.append(lockserver.do_start_session())

    # First session requests lock on the user 'bob'.
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[0], locks)
    
    # First session requests locks on the nodes '123' and '456'.
    locks = {'node':['123','456']}
    lockserver.do_acquire_locks(sess[0], locks)

    # Second session requests lock on the node '123'.
    locks = {'node':['123']}
    lockserver.do_acquire_locks(sess[1], locks)

    # Third session requests lock on the user 'bob'.
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[2], locks)

    expected_heldlockdict = {
      'user': {'bob': {'locked_by_session': sess[0],
                       'queue': [sess[2]]}},
      'node': {'123': {'locked_by_session': sess[0],
                       'queue': [sess[1]]},
               '456': {'locked_by_session': sess[0],
                       'queue': []}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': ['bob'], 'node': ['123','456']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False},
      sess[2]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': ['bob'], 'node': []},
                'acquirelocksproceedeventset': False}}

    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])

    # First session releases user lock on 'bob'.
    # Note: they still hold the node locks on '123' and '456'
    locks = {'user':['bob']}
    lockserver.do_release_locks(sess[0], locks)

    expected_heldlockdict = {
      'user': {'bob': {'locked_by_session': sess[2],
                       'queue': []}},
      'node': {'123': {'locked_by_session': sess[0],
                       'queue': [sess[1]]},
               '456': {'locked_by_session': sess[0],
                       'queue': []}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': [], 'node': ['123','456']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False},
      sess[2]: {'heldlocks': {'user': ['bob'], 'node': []},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True}}

    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])

    # First session releases node lock on '123'.
    # Note: they still hold the node lock on '456'
    locks = {'node':['123']}
    lockserver.do_release_locks(sess[0], locks)

    expected_heldlockdict = {
      'user': {'bob': {'locked_by_session': sess[2],
                       'queue': []}},
      'node': {'123': {'locked_by_session': sess[1],
                       'queue': []},
               '456': {'locked_by_session': sess[0],
                       'queue': []}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': [], 'node': ['456']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[1]: {'heldlocks': {'user': [], 'node': ['123']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'user': ['bob'], 'node': []},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True}}

    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])

    # First session releases node lock on '456' and then requests locks on
    # user 'bob' and nodes '123' and '456' again. It can't request the node
    # locks, however, until it gets the node lock (in xmlrpc usage, the
    # user lock request would have blocked). So, we have the session that is
    # holding the lock on user 'bob' release that lock before the first session
    # makes the node lock requests.
    locks = {'node':['456']}
    lockserver.do_release_locks(sess[0], locks)
    locks = {'user':['bob']}
    lockserver.do_acquire_locks(sess[0], locks)
    locks = {'user':['bob']}
    lockserver.do_release_locks(sess[2], locks)
    locks = {'node':['123', '456']}
    lockserver.do_acquire_locks(sess[0], locks)
        
    expected_heldlockdict = {
      'user': {'bob': {'locked_by_session': sess[0],
                       'queue': []}},
      'node': {'123': {'locked_by_session': sess[1],
                       'queue': [sess[0]]},
               '456': {'locked_by_session': sess[0],
                       'queue': []}}}
    expected_sessiondict = {
      sess[0]: {'heldlocks': {'user': ['bob'], 'node': ['456']},
                'neededlocks': {'user': [], 'node': ['123']},
                'acquirelocksproceedeventset': False},
      sess[1]: {'heldlocks': {'user': [], 'node': ['123']},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True},
      sess[2]: {'heldlocks': {'user': [], 'node': []},
                'neededlocks': {'user': [], 'node': []},
                'acquirelocksproceedeventset': True}}

    status = lockserver.do_get_status()
    self.assertEqual(expected_heldlockdict, status["heldlockdict"])
    self.assertEqual(expected_sessiondict, status["sessiondict"])
