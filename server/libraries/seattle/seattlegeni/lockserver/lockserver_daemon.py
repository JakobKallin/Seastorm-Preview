"""
<Program>
  lockserver_daemon.py

<Started>
  30 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is the XML-RPC Lockserver that is used by various components of
  SeattleGeni.
 
  Two lock types are supported: 'user' and 'node'.
 
  Multiple of the same lock type ('user' or 'node') can be requested at
  the same time, but a single lock acquisition request cannot include
  requests for both types of locks.
 
  Clients first request a session identifier from the lockserver and
  then make requests for acquiring and releasing locks using that
  session identifier. It is the client's responsibility to release any
  lock they have acquired and to let the lockserver know when they
  are finished with their session (that is, when they have released
  all of their locks and do not plan to acquire more locks in the
  same session).
 
  Clients are denied lock acquisition requests as follows:
    * If the client's session already holds 'user' locks and the client is
      requesting 'user' locks.
    * If the client's session already holds 'node' locks.
    * If the client's session has any pending (unfulfilled) lock requests.

  That is, a client must (in a given session) request and obtain user locks
  before requesting node locks if the client intends to hold both kinds of
  locks at the same time.
 
  If clients hold both user locks and node locks, the locks can be released
  in any order. As per the restrictions on lock acquisition, though, the
  client won't be able to obtain additional node locks until they have
  released all of the node locks they hold. They will also not be able
  to obtain additional user locks until they have released all of their locks.


XML-RPC Interface:
 
StartSession()
  <Purpose>
    Obtain a new session identifier that can be used to acquire/release locks.
  <Arguments>
    None.
  <Exceptions>
    None.
  <Side Effects>
    The new session identifier is reserved within the lockserver.
  <Returns>
    Returns a string with a new session id. The value will be unique with
    respect to all session ids currently being tracked by the lockserver.
 
EndSession(session_id_str)
  <Purpose>
    Destroys the specified session.
  <Arguments>
    session_id_str: the session id
  <Exceptions>
    This will evoke an xmlrpclib.Fault exception on the client side if the session
    does not exist or if the session has locked resources or pending lock requests.
  <Side Effects>
    Removes all information about the specified session.
    Since an Exception will occur if the session holds any locks or has any
    pending lock requests, it is mostly just removing the record of the session
    identifier.
  <Returns>
    None.
        
AcquireLocks(session_id_str, lockdict)
  <Purpose>
    Obtain a lock on one or more lock names of a given type. This is a blocking
    request.
  <Arguments>
    session_id_str: the session id
    lockdict: a "lockdict" (see notes below)
  <Exceptions>
    This will evoke an xmlrpclib.Fault exception on the client side if the request
    is for locks the client shouldn't be requesting. See the notes above that give 
    the reasons clients will be denied lock acquisition.
  <Side Effects>
    Blocks until all of the locks specified in the lockdict are obtained for
    the specified session.
  <Returns>
    None.
 
ReleaseLocks(session_id_str, lockdict)
  <Purpose>
    Release one or more locks of one or more types.
  <Arguments>
    session_id_str: the session id
    lockdict: a "lockdict" (see notes below)
  <Exceptions>
    This will evoke an xmlrpclib.Fault exception on the client side if the session
    does not hold one or more of the locks that are listed in the lockdict.
  <Side Effects>
    Releases the locks previously held by the session. The released locks
    will be immediately obtained by other sessions waiting on the same
    lock.
  <Returns>
    None.
 
GetStatus()
  <Purpose>
    Obtains information about locks that are held, who holds them, and
    what locks are needed by any sessions that are waiting on locks.
    This allows observing the current state of the lockserver.
  <Arguments>
    None.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A dictionary with the keys, "heldlockdict",  "sessiondict", and
    "locktimelist" is returned. The values of these keys are most of the
    contents of the global variables by the same names used within the
    lockserver itself. It excludes the Event objects from the sessiondict
    data that is returned.

 
Details of the "lockdict" format:
  The lockdict format is a dictionary with two possible valid keys, 'user'
  and 'node'. If the key exists, its value must be a list of strings. Each
  of the strings specifies the name of a lock (whose type is either 'user'
  or 'node').
   
  Examples of valid lockdicts:
    {'user':['bob']}
    {'node':['123','xyz']}
    {'user':['bob'], 'node':['123','xyz']}
   
  The last one above, {'node': ['bob'], 'user': ['123','xyz']}, would not
  be valid for an AcquireLocks request because it lists two different
  types of locks (both 'user' and 'node'). It would, however, be valid for a
  ReleaseLocks request.
   
  Examples of invalid lockdicts:
    {}
    {'user':None}
    {'user':[123]}     # the name of the lock must be a string, '123'
    {'user':[]}        # an empty list of names is not valid
    {'x':['bob']}      # 'x' is not a valid locktype (only 'user' and 'node')
 
 
<Notes> 
  The lock type of 'global' has not been implemented as there is no clear need
  for it at this time and it would increase complexity.
 
  The lockserver does not perform special handling of requests that disconnect
  from the server during a lock acquisition request. The client's session will
  ultimately be granted the locks (assuming it was a valid request).
 
  This implementation does not allow an individual session to make additional
  lock acquisition requests while an existing lock acquisition request by the
  same session is unfulfilled. It doesn't seem like it would be correct
  behavior on behalf of a client to do so, so it's not supported. One case
  where this might be an issue is with parallelized work by the same client
  code using the same session id.
 
 
  General overview of the code: 
 
  The functions that can be called through the xmlrpc interface are the the 
  public functions in the class called LockserverPublicFunctions. Each of those 
  functions sanitizes user input, obtains a global datalock (of which there is 
  one in the entire module), and calls a helper function to do the actual work. 
  The helper function for any public xmlrpc function named MyFunction is of the
  format do_my_function. The global datalock is not used anywhere but
  in the methods of LockserverPublicFunctions. All other code that modifies
  global data assumes that the global datalock is held.
 
  Each session is only allowed to make one call to AcquireLocks at a time.
  This is enforced by disallowing AcquireLocks setting a boolean flag in
  the data for that session to indicate the session has a pending AcquireLocks
  request.
 
  The blocking of request threads when all locks are not yet available is
  handled through the use of threading.Event() objects. Each session has
  a single Event() object. A single Event per session is adequate because
  each session is only allowed to make one AcquireLocks call at a time.
  The AcquireLocks call will wait on the session's Event object until
  it has been set, which is the signal that all of the requested locks
  have been acquired for that session. The event can either be set/signaled
  as a result of the AcquireLocks call (if all of the locks are available
  at the time of the request) or by ReleaseLocks calls made by any session
  (if a lock that is released leaves the blocked AcquireLocks request
  with no more locks needing to be acquired).
 

<TODOs>
  TODO: Test to find out how many blocked threads can be supported.
  TODO: Test that a blocked lock request will not disconnect if it
        is blocked for a very long time.
  TODO: Write more integration tests (at least to test invalid requests).
  TODO: Write a simple benchmark script.
"""

import datetime

import time
import sys

# To send the admins emails when there's an unhandled exception.
import django.core.mail 

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import log

from seattlegeni.website import settings

# Use threading.Lock directly instead of repy's getlock() to ease testing
# by not depending on repy. We also use threading.Event().
import threading

# To start the background monitor_held_lock_times() thread.
import thread

import traceback

# These are used to build a single-threaded XMLRPC server.
import SocketServer
import SimpleXMLRPCServer

# Used to generate session ids.
import random



# The port that we'll listen on.
LISTENPORT = 8010

# Session ids will be random numeric strings between these two values, inclusive.
MIN_SESSION_ID = 1000000
MAX_SESSION_ID = 9999999

# This is the amount of time the longest-held lock is allowed to be held before
# we consider there to be something very wrong and send notification emails to
# administrators.
MAX_EXPECTED_LOCK_HOLDING_TIMEDELTA = datetime.timedelta(minutes=5)

# Number of seconds to wait between checks of whether a lock has been held too
# long.
SECONDS_BETWEEN_LOCK_HOLDING_TIME_CHECKS = 30






# Whether the lockserver encountered an error. The server server thread will
# use this to decide whether to exit.
lockserver_had_error = False

# A mutex for access to all shared data.
datalock = threading.Lock()

# Format is not the same as the lockdict described in the module comments at the top:
#heldlockdict = {
#                "user"
#                  "bob" : {
#                    "queue" : [list_of_session_ids],
#                    "locked_by_session" : None
#                  },
#                  ... 
#                },        
#                "node"
#                  [same as "user", that is, each node has its own key and the
#                   value is a dict containing keys "queue" and "locked_by_session"]
#                },     
#}
# Note: This value is initialized by the call to init_globals()
heldlockdict = None

# Keeps track of which locks are held by which lockserver clients.
# The keys are lockserver session ids and the values are dictionaries of locks
# that are held by that session id.
# Format is not the same as the lockdict described in the module comments at the top:
#sessiondict = {
#                "abc123" : {
#                  "heldlocks" : {
#                    "user" : [list_of_user_name_strings],
#                    "node" : [list_of_node_name_strings]
#                  },
#                  "neededlocks" : lockdict only containing unfulfilled items,
#                  "acquirelocksproceedevent" : Event object used to block an AcquireLocks request until it is fulfilled,
#                  "acquirelocksinprogress" : boolean value to indicate whether an AcquireLocks request is in progress
#                }
#              }
# Note: This value is initialized by the call to init_globals()
sessiondict = None

# This is a list of tuples of the format ({locktype: lockname}, locktime) 
# containing an entry for every acquired lock. The locktime is a datetime
# object representing the time when the lock was acquired. The list is in
# order where the first item in the list is the longest-held lock and the
# last item is the shortest-held lock. The reason this information is not
# just kept in the heldlockdict is largely because we don't want to return
# the time in with the GetStatus call because the tests would have to be
# changed to expect a value there that is different with every run of the
# test. Also, all we really care about is the longest-held lock and most
# of the point here is to be able to detect when any lock has been held
# past a threshold that we consider reasonable. So, for that, we might
# as well keep track of the order explicitly as we know that information
# here in the lockserver daemon.
locktimelist = []





class ThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  """This is a threaded XMLRPC Server. """




  
class LockserverInvalidRequestError(Exception):
  """Indicates that an invalid request was made by the client."""





def _lockdict_contains_lock(lockdict, locktype, lockname):
  """
  Returns True if a lock of the specified locktype and lockname is in lockdict,
  otherwise returns False.
  """
  if locktype in lockdict:
    if lockname in lockdict[locktype]:
      return True
  return False





def _is_lockdict_empty(lockdict):
  """
  Returns True if there are no locks specified in the lockdict, otherwise
  returns False. Note that there must be at least one lock name defined
  for at least one lock locktype for there to be considered a lock in the
  lockdict.
  """
  for locktype in lockdict:
    if len(lockdict[locktype]) > 0:
      return False
  return True





def init_globals():
  """
  <Purpose>
    Prepares the global variables heldlockdict and sessiondict. They
    are set this way rather than directly when declared as this this method is
    needed for unit tests that work directly with the lockserver_daemon module
    rather than starting and stopping the lockserver and using xmlrpc. This
    method should never be called after the lockserver is running.
  <Arguments>
    None.
  <Exceptions>
    None.
  <Side Effects>
    Resets the heldlockdict and sessiondict global variables, thus clearing
    the state of the lockserver.
  <Returns>
    None.
  """
  
  global heldlockdict
  global sessiondict

  heldlockdict = {"user":{}, "node":{}}
  sessiondict = {}
  
  
  


def _generate_session_id():
  """
  Generates a session id that doesn't already exist in the sessiondict. The
  created session id is a numeric string between MIN_SESSION_ID and
  MAX_SESSION_ID. We create intentionally random session ids rather than
  assigning them sequentially to reduce the risk of clients accidentally using 
  a session id that really isn't theirs.
  """
  session_id = None
  while session_id is None or session_id in sessiondict:
    session_id = str(random.randint(MIN_SESSION_ID, MAX_SESSION_ID))
    
  return str(session_id)





def do_start_session():
  """
  <Purpose>
    This is the function that does the actual work for xmlrpc calls to
    StartSession. The caller of this function must hold the global datalock.
  <Arguments>
    None.
  <Exceptions>
    None.
  <Side Effects>
    The new session id is added to the global sessiondict.
  <Returns>
    The newly-created session id.
  """
  session_id = _generate_session_id()
  
  sessiondict[session_id] = {}
  
  # The Event object is to cause lock acquisition requests by this session to
  # block until the request has been fulfilled.
  sessiondict[session_id]["acquirelocksproceedevent"] = threading.Event()
  # Have the event be initially set. This is so that we can know that the
  # event is only unset (clear) if an AcquireLocks thread is blocked and
  # waiting for locks it needs to acquire. Though the code should work
  # fine even if we don't set this here, it's better to be able to conclusively
  # determine whether a session has a blocked AcquireLocks request by inspecting
  # this (making testing and debugging easier).
  sessiondict[session_id]["acquirelocksproceedevent"].set()
  
  # Indicate whether there is a current AcquireLocks call that has not been
  # fulfilled yet. We use this so that an AcquireLocks request thread can
  # indicate that it has proceeded past its event wait() call and thus the
  # same session is allowed to make further AcquireLocks requests.
  sessiondict[session_id]["acquirelocksinprogress"] = False

  # Create empty lockdicts with "user" and "node" keys for indicating the
  # locks the session holds and the locks the session is queued for.
  sessiondict[session_id]["heldlocks"] = {"user":[], "node":[]}
  sessiondict[session_id]["neededlocks"] = {"user":[], "node":[]}
  
  return session_id





def do_end_session(session_id):
  """
  <Purpose>
    This is the function that does the actual work for xmlrpc calls to
    EndSession. The caller of this function must hold the global datalock.
  <Arguments>
    session_id:
      The string that is the session id to be ended.
  <Exceptions>
    LockserverInvalidRequestError is raised if the specified session does
    not exist, if it still holds locks, or if it has pending, unfulfilled
    lock acquisition requests.
  <Side Effects>
    If no exception occurs, the specified session is removed from the
    global sessiondict.
  <Returns>
    None.
  """
  # Raises an exception if the session id doesn't exist.
  _assert_valid_session(session_id)
    
  if not _is_lockdict_empty(sessiondict[session_id]["heldlocks"]):
    raise LockserverInvalidRequestError("Cannot end session: this session still holds locks.")
    
  if not _is_lockdict_empty(sessiondict[session_id]["neededlocks"]):
    raise LockserverInvalidRequestError("Cannot end session: this session has pending queued lock requests.")
    
  # Get rid of the session.
  del sessiondict[session_id]
    




def do_acquire_locks(session_id, requested_acquire_lockdict):
  """
  <Purpose>
    This is the function that does the actual work for xmlrpc calls to
    AcquireLocks. Other than for testing, this should only be called by the
    AcquireLocks function registered with the xmlrpc server.
    The caller of this function must hold the global datalock.
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be acquired.
    requested_acquire_lockdict:
      The lockdict that contains the locks to be acquired.
  <Exceptions>
    LockserverInvalidRequestError is raised if the specified session is
    invalid or the requested locks are invalid (including whether they are
    invalid based on locks the session holds or previous lock acquisitions
    requests that have not been fulfilled yet).
  <Side Effects>
    Each specified lock is either immediately granted (if no other session
    holds it) or this session is added to a queue for that lock. The Event
    that belongs the specified session is reset (cleared) to ensure the
    server's thread handling this request blocks. As soon as all of the
    requested locks are held, the Event is used to allow the server's thread
    to proceed (and thus respond to the client).
  <Returns>
    None.
  """
  # Raises an exception if the session id doesn't exist.
  _assert_valid_session(session_id)
  
  # Raises an exception if the lockdict format is invalid.
  _assert_valid_lockdict(requested_acquire_lockdict)
  
  # Raises an exception if the requested locks are invalid, including if they
  # conflict with ones held by the same session.
  _assert_valid_locks_for_acquire(session_id, requested_acquire_lockdict)
  
  for locktype in requested_acquire_lockdict:
    for lockname in requested_acquire_lockdict[locktype]:
      _acquire_individual_lock(session_id, locktype, lockname)
      
  # Check if the request got all of the locks it asked for in order to
  # determine whether the request thread should block.
  if _is_lockdict_empty(sessiondict[session_id]["neededlocks"]):
    # It did get all of the locks it asked for, so the request thread shouldn't block.
    sessiondict[session_id]["acquirelocksproceedevent"].set()
  else:
    # It did not get all of the locks it asked for, so the request thread should block.
    sessiondict[session_id]["acquirelocksproceedevent"].clear()





def _acquire_individual_lock(session_id, locktype, lockname):
  """
  <Purpose>
    This is called by do_acquire_locks for each lock to be acquired. This will
    either mark the lock as being held by the specified session (if the lock
    is not already held) or will add this session the lock's queue (if the
    lock is already held).
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be acquired.
    locktype:
      The locktype of lock, either 'user' or 'node'.
    lockname:
      The lockname of the lock (a string).
  <Exceptions>
    None.
  <Side Effects>
    Modifies the global heldlockdict and the global sessiondict based on
    whether the lock is immediately given to the session or whether the
    session has been put in the lock's queue.
  <Returns>
    None.
  """
  # Create the lock info if it didn't already exist in the global heldlockdict.
  if not lockname in heldlockdict[locktype]:
    heldlockdict[locktype][lockname] = {"queue":[], "locked_by_session":None}

  heldlockinfo = heldlockdict[locktype][lockname]
  
  if heldlockinfo["locked_by_session"] is None:
    # Nobody holds this lock, so give it to this session.
    heldlockinfo["locked_by_session"] = session_id
    
    # Record in the sessiondict that the session holds this lock.
    sessiondict[session_id]["heldlocks"][locktype].append(lockname)
    
    # Append to the locktimelist indicating when this lock was acquired.
    locktimelist.append(({locktype: lockname}, datetime.datetime.now()))
    
  else:
    # This lock is already held, so add the session to this lock's queue.
    heldlockinfo["queue"].append(session_id)
    
    # Record in the sessiondict that this session is waiting on this lock.
    sessiondict[session_id]["neededlocks"][locktype].append(lockname)





def _assert_valid_locks_for_acquire(session_id, requested_acquire_lockdict):
  """
  <Purpose>
    Ensures that the locks specified in requested_acquire_lockdict are locks
    that the given session should legitimately be requesting. That is,
    ensures they aren't locks the session already holds, ensures that the
    session should even be requesting locks at all (e.g. do they have a pending
    lock request?), checks if they are requesting a 'user' lock even though
    they already hold a 'node' lock, etc.
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be acquired.
    requested_acquire_lockdict:
      The lockdict that contains the locks to be acquired.
  <Exceptions>
    Raises LockserverInvalidRequestError if requested_acquire_lockdict contains
    locks that would be invalid for this session to request acquisition of.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  # Check if the session is requesting locks of both type "user" and type "node".
  if len(requested_acquire_lockdict.keys()) != 1:
    # Raise an error that will be returned over xmlrpc.
    message = "Requested acquisition of locks of multiple types (you can only request locks of a single type at a time)."
    _raise_lock_request_error(session_id, requested_acquire_lockdict, message)
  
  # Locks of the same locktype as those already held cannot be requested.
  for locktype in requested_acquire_lockdict:
    # Check if the session already holds locks of this locktype.
    if len(sessiondict[session_id]["heldlocks"][locktype]) > 0:
      # Raise an error that will be returned over xmlrpc.
      message = "Requested acquisition of locks of same locktype ('" + locktype + "') as those already held by this session."
      _raise_lock_request_error(session_id, requested_acquire_lockdict, message)

  # User locks cannot be requested when a node lock is already held.
  if "user" in requested_acquire_lockdict:
    # Check if the session already holds locks of the 'node' locktype.
    if len(sessiondict[session_id]["heldlocks"]["node"]) > 0:
      # Raise an error that will be returned over xmlrpc.
      message = "Requested acquisition of user lock when node locks already held by this session."
      _raise_lock_request_error(session_id, requested_acquire_lockdict, message)

     
    
    

def do_release_locks(session_id, requested_release_lockdict):
  """
  <Purpose>
    This is the function that does the actual work for xmlrpc calls to
    ReleaseLocks. Other than for testing, this should only be called by the
    ReleaseLocks function registered with the xmlrpc server.
    The caller of this function must hold the global datalock.
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be released.
    requested_release_lockdict:
      The lockdict that contains the locks to be released.
  <Exceptions>
    LockserverInvalidRequestError is raised if the specified session is
    invalid or if any of the locks requested to be released are not
    held by the session.
  <Side Effects>
    Each specified lock is immediately released. For any released lock, if
    there is a session waiting (queued) for the lock, the next queued session
    is given the lock (and the waiting thread unblocked if they do not
    require any more locks).
  <Returns>
    None.
  """
  # Raises an exception if the session id doesn't exist.
  _assert_valid_session(session_id)
  
  # Raises an exception if the lockdict format is invalid.
  _assert_valid_lockdict(requested_release_lockdict)
  
  # Raises an exception if the requested locks for release are invalid, including
  # if they are not all held by this session.
  _assert_valid_locks_for_release(session_id, requested_release_lockdict)
  
  for locktype in requested_release_lockdict:
    for lockname in requested_release_lockdict[locktype]:
      _release_individual_lock(session_id, locktype, lockname)





def _release_individual_lock(session_id, locktype, lockname):
  """
  <Purpose>
    This is called by do_release_locks for each lock to be released. This will
    mark the lock as not being held by the specified session and will take care
    of giving released locks to queued requests.
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be released.
    locktype:
      The locktype of lock, either 'user' or 'node'.
    lockname:
      The lockname of the lock (a string).
  <Exceptions>
    None.
  <Side Effects>
    Modifies the global heldlockdict and the global sessiondict to indicate
    that the specified lock is no longer held by the session as well as to
    grant the lock to the next session in the lock's queue which is waiting
    for it, if any. If there was a session queued for this lock, after
    giving the lock to that session this function will check if the new
    lock holder is waiting on any more locks. If not, the server thread
    for the queued request will be unblocked.
  <Returns>
    None.
  """
  heldlockinfo = heldlockdict[locktype][lockname]
  
  # Regardless of whether there are queued sessions waiting for this lock,
  # it is removed from the list of locks this session holds.
  sessiondict[session_id]["heldlocks"][locktype].remove(lockname)

  # Remove this lock from the locktimelist.
  for locktimeitem in locktimelist:
    if locktimeitem[0] == {locktype: lockname}:
      log.info("Lock " + str({locktype: lockname}) + " was held for " + 
               str(datetime.datetime.now() - locktimeitem[1]))
      locktimelist.remove(locktimeitem)
      break
  
  if len(heldlockinfo["queue"]) > 0:
    # Set the lock as held by the next queued session_id.
    new_lock_holder = heldlockinfo["queue"].pop(0)
    heldlockinfo["locked_by_session"] = new_lock_holder
    
    # Update the sessiondict to change this lock from a needed lock to a held lock.
    sessiondict[new_lock_holder]["heldlocks"][locktype].append(lockname)
    sessiondict[new_lock_holder]["neededlocks"][locktype].remove(lockname)
    
    # Append to the locktimelist indicating when this lock was acquired.
    locktimelist.append(({locktype: lockname}, datetime.datetime.now()))
    
    # If the session  now holding the lock isn't waiting on any more locks,
    # unblock the session's current AcquireLocks request thread.
    if _is_lockdict_empty(sessiondict[new_lock_holder]["neededlocks"]):
      sessiondict[new_lock_holder]["acquirelocksproceedevent"].set()
    
  else:
    # There are no sessions waiting on this lock, so the lock is now held by nobody.
    heldlockinfo["locked_by_session"] = None
    
    
    
    
    
def _assert_valid_locks_for_release(session_id, requested_release_lockdict):
  """
  <Purpose>
    Ensures that the locks specified in requested_acquire_lockdict are locks
    that the given session should legitimately be trying to release. That is,
    ensures the session holds all of the locks specified in the lockdict.
  <Arguments>
    session_id:
      The string that is the session id under which the locks should be released.
    requested_release_lockdict:
      The lockdict that contains the locks to be released.
  <Exceptions>
    Raises LockserverInvalidRequestError if requested_release_lockdict contains
    any locks that the session does not hold.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  sessionheldlockdict = sessiondict[session_id]["heldlocks"]
  
  # Go through the locks being requested for release and if any of them aren't
  # currently held by this session, raise an error.
  for locktype in requested_release_lockdict:
    for lockname in requested_release_lockdict[locktype]:
      if not _lockdict_contains_lock(sessionheldlockdict, locktype, lockname):
        # Raise an error that will be returned over xmlrpc.
        message = "Attempted to release locks not held by this session."
        _raise_lock_request_error(session_id, requested_release_lockdict, message)
    
  # Should we make sure the client isn't releasing a user lock while they still
  # hold node locks? There may not be any deadlock risk that results from
  # this, but it is likely incorrect behavior. Not forbidding it for now.




def do_get_status():
  """
  <Purpose>
    This is the function that does the actual work for xmlrpc calls to
    GetStatus. Other than for testing, this should only be called by the
    GetStatus function registered with the xmlrpc server.
    The caller of this function must hold the global datalock.
  <Arguments>
    None.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A dictionary with the keys, "heldlockdict",  "sessiondict", and
    "locktimelist" is returned. The values of these keys are most of the
    contents of the global variables by the same names used within the
    lockserver itself. It excludes the Event objects from the sessiondict
    data that is returned.
  """

  # We create a sessiondict that 
  cleansessiondict = {}
  for session_id in sessiondict:
    cleansessiondict[session_id] = {}
    cleansessiondict[session_id]["heldlocks"] = sessiondict[session_id]["heldlocks"]
    cleansessiondict[session_id]["neededlocks"] = sessiondict[session_id]["neededlocks"]
    
    # We include a acquirelocksproceedeventset value in the status info rather than the
    # boolean acquirelocksinprogress value because we want to be able to test without
    # running the xmlrpc server. That is, the unit tests that make direct
    # calls to do_acquire_locks() and do_release_locks() won't see a useful value 
    # for acquirelocksinprogress because that is only set directly in AcquireLocks.
    # However, the event that is waited on is set and cleared in in the
    # do_acquire_locks() and do_release_locks() functions, so it is useful for
    # unit testing (the code was intentionally organized to make that testable).
    # Note: python <2.6 only supports isSet(), not is_set().
    acquirelocksproceedeventset = sessiondict[session_id]["acquirelocksproceedevent"].isSet()
    cleansessiondict[session_id]["acquirelocksproceedeventset"] = acquirelocksproceedeventset
  
  status = {}
  status["heldlockdict"] = heldlockdict
  status["sessiondict"] = cleansessiondict
  status["locktimelist"] = locktimelist
  return status
    
    



def _assert_number_of_arguments(functionname, args, exact_number):
  """
  <Purpose>
    Ensure that an args tuple which one of the public xmlrpc functions was
    called with has an expected number of arguments.
  <Arguments>
    functionname:
      The name of the function whose number of arguments are being checked.
      This is just for logging in the case that the arguments don't match.
    args:
      A tuple of arguments (received by the other function through *args).
    exact_number:
      The exact number of arguments that must be in the args tuple.
  <Exceptions>
    Raises LockserverInvalidRequestError if args does not contain exact_number
    items.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  if len(args) != exact_number:
    message = "Invalid number of arguments to function " + functionname + ". "
    message += "Expected " + str(exact_number) + ", received " + str(len(args)) + "."
    raise LockserverInvalidRequestError(message)





def _assert_valid_session(session_id):
  """
  <Purpose>
    Ensure that a session id received by a call to a public xmlrpc function
    is a valid session id (not just in format, but that the session was
    started and has not already been ended).
  <Arguments>
    session_id:
      The session id string to check.
  <Exceptions>
    Raises LockserverInvalidRequestError if session_id is not an existing
    session id.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  if not isinstance(session_id, str):
    raise LockserverInvalidRequestError("Invalid session id (must be a string). You provided a " + str(type(session_id)) + " which was " + str(session_id))
  if session_id not in sessiondict:
    raise LockserverInvalidRequestError("Invalid session id (the specified session id doesn't exist).")





def _assert_valid_lockdict(lockdict):
  """
  <Purpose>
    Ensures that the specified lockdict (which comes from user input) is of an
    acceptable format.
  <Arguments>
    lockdict:
      The lockdict to check.
  <Exceptions>
    Raises LockserverInvalidRequestError the specified lockdict is illegal for
    any reason (e.g. isn't a dictionary, specifies lock types that are invalid,
    etc.)
  <Side Effects>
    None.
  <Returns>
    None.
  """
  if not isinstance(lockdict, dict):
    raise LockserverInvalidRequestError("Invalid lockdict (lockdict must be a dict).")
  
  if len(lockdict.keys()) == 0:
    raise LockserverInvalidRequestError("Invalid lockdict (must specify at least one locktype of lock).")

  for locktype in lockdict:
    if not isinstance(lockdict[locktype], list):
      raise LockserverInvalidRequestError("Invalid lockdict (each key's value must be a list of locknames).")
    
    if locktype not in ["user", "node"]:
      # Even though xmlrpclib doesn't allow non-strings for dict keys, python does.
      # So, to be proper/safe, we cast 'locktype' to a string.
      raise LockserverInvalidRequestError("Invalid lockdict (lock locktype '" + str(locktype) + "' does not exist).")
    
    if len(lockdict[locktype]) == 0:
      raise LockserverInvalidRequestError("Invalid lockdict (no lock names specified for lock locktype '" + locktype + "').")

    for lockname in lockdict[locktype]:
      if not isinstance(lockname, str):
        raise LockserverInvalidRequestError("Invalid lockdict (all items in a list of locknames must be str's).")
      if len(lockname) == 0:
        raise LockserverInvalidRequestError("Invalid lockdict (lock names cannot be empty strings).")
      if len(lockdict[locktype]) != len(set(lockdict[locktype])):
        raise LockserverInvalidRequestError("Invalid lockdict (all items in a list of locknames must unique in that list).")
      




def _raise_lock_request_error(session_id, lockdict_in_request, message):
  """
  Raises a LockserverInvalidRequestError with a description that includes
  the given session_id, lockdict_in_request, and message, as well as
  the session's held locks and pending locks.
  """
  requested_lock_str = str(lockdict_in_request)
  
  sessionheldlockdict = sessiondict[session_id]["heldlocks"]
  held_locks_str = str(sessionheldlockdict)
  
  sessionneededlockdict = sessiondict[session_id]["neededlocks"]
  needed_locks_str = str(sessionneededlockdict)
  
  info_str = "Session id: " + session_id + ". "
  info_str += "Locks in request: " + requested_lock_str + ". "
  info_str += "Held locks: " + held_locks_str + ". "
  info_str += "Pending locks: " + needed_locks_str + "."
  
  raise LockserverInvalidRequestError("Illegal request: " + message + " [" + info_str + "]")





class LockserverPublicFunctions(object):
  """
  All public functions of this class are automatically exposed as part of the
  xmlrpc interface.
  """
  
  def _dispatch(self, method, args):
    """
    We provide a _dispatch function (which SimpleXMLRPCServer looks for and
    uses) so that we can log exceptions due to our programming errors within
    thelockserver as well to detect incorrect usage by clients. When an
    internal lockserver error is detected, this method will signal to the main
    server thread to shutdown.
    """
    global lockserver_had_error
      
    try:
      # Get the requested function (making sure it exists).
      try:
        func = getattr(self, method)
      except AttributeError:
        raise LockserverInvalidRequestError("The requested method '" + method + "' doesn't exist.")
      
      # Call the requested function.
      return func(*args)
    
    except LockserverInvalidRequestError:
      log.error("The lockserver was used incorrectly: " + traceback.format_exc())
      raise
    
    except:
      # We assume all other exceptions are bugs in the lockserver.
      # If there is a bug in the lockserver, that's really bad. We terminate the
      # lockserver in this case rather than risk incorrect locking behavior.
      
      # This will tell the server thread to exit.
      lockserver_had_error = True

      message = "The lockserver had an internal error and is exiting." + traceback.format_exc()
      log.critical(message)

      # Send an email to the addresses listed in settings.ADMINS
      if not settings.DEBUG:
        subject = "Critical SeattleGeni lockserver error"
        django.core.mail.mail_admins(subject, message)
      
      # This request will likely end up seeing an xmlrpclib.ProtocolError due to the
      # shutdown, regardless of this exception.
      raise



  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  def StartSession(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('StartSession', args, 0)
    
    datalock.acquire()
    try:
      session_id = do_start_session()
      
      log.info("[session_id: " + session_id + "] StartSession called.")
      
      return session_id
    
    finally:
      datalock.release()
      
      
      
  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  def EndSession(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('EndSession', args, 1)
    # avoid python magic comma needed to write this as "(session_id,) = args"
    session_id = args[0]
    
    datalock.acquire()
    try:
      # Ensure it's a string before printing it like one.
      _assert_valid_session(session_id)
      
      log.info("[session_id: " + session_id + "] EndSession called.")
      
      do_end_session(session_id)
      
    finally:
      datalock.release()
      


  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  def AcquireLocks(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('AcquireLocks', args, 2)
    (session_id, request_acquire_lockdict) = args
    
    datalock.acquire()
    try:
      # Ensure it's a string before printing it like one.
      _assert_valid_session(session_id)
      
      log.info("[session_id: " + session_id + "] AcquireLocks called for locks " + str(request_acquire_lockdict))
    
      # Check if this session has an outstanding AcquireLocks request. Clients
      # should not be making concurrent AcquireLocks requests.
      if sessiondict[session_id]["acquirelocksinprogress"]:
        message = "[session_id: " + session_id + "] AcquireLocks called while an earlier AcquireLocks call has not been completed."
        raise LockserverInvalidRequestError(message)
      
      do_acquire_locks(session_id, request_acquire_lockdict)
      
      # Indicate that there is a running AcquireLocks request for this session
      # so that future AcquireLocks requests will be denied until this one is
      # fulfilled. If the call to do_acquire_locks raised an exception, this
      # will not get set.
      sessiondict[session_id]["acquirelocksinprogress"] = True
      
    finally:
      datalock.release()
    
    # Wait for our event flag to signal that we have acquired the locks.
    # This is what causes the request thread to block until it is fulfilled.
    # If the event is not set at this point (causing this thread to block),
    # then it will be set by calls to ReleaseLocks. If a call to ReleaseLocks
    # signals this event between the time we released the global datalock and
    # when we get to this wait() line, that's fine.
    sessiondict[session_id]["acquirelocksproceedevent"].wait()
    
    # Indicate that we've made it past our wait() call, meaning that future
    # calls to do_acquire_locks() can be allowed again. We do not need to hold
    # the global datalock to set this as it can only be set to True in the
    # critical section above which first ensures that the value is not already
    # true.
    sessiondict[session_id]["acquirelocksinprogress"] = False
    
    log.info("[session_id: " + session_id + "] AcquireLocks fulfilled request for locks " + str(request_acquire_lockdict))
    


  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  def ReleaseLocks(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('ReleaseLocks', args, 2)
    (session_id, request_release_lockdict) = args
  
    datalock.acquire()
    try:
      # Ensure it's a string before printing it like one.
      _assert_valid_session(session_id)
      
      log.info("[session_id: " + session_id + "] ReleaseLocks called for locks " + str(request_release_lockdict))
      
      do_release_locks(session_id, request_release_lockdict)
      
    finally:
      datalock.release()
  
  
  
  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  def GetStatus(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('GetStatus', args, 0)
    
    datalock.acquire()
    try:
      log.info("GetStatus called.")
      return do_get_status()
    finally:
      datalock.release()





def monitor_held_lock_times():
  """
  Periodically checks whether there are locks that have been held too long.
  When there is a lock that has been held too long, logs it and also sends
  an email if settings.DEBUG is False.
  
  This function gets started in its own thread.
  """
  
  log.info("[monitor_held_lock_times] thread started.")

  # Run forever.
  while True:
    
    try:
      
      # Wait a bit between checks.
      time.sleep(SECONDS_BETWEEN_LOCK_HOLDING_TIME_CHECKS)
      
      # Grab the datalock and get the oldest held lock, if there are any.
      datalock.acquire()
      try:
        if len(locktimelist) == 0:
          # No locks are held.
          continue
        
        oldestlock = locktimelist[0]
        
      finally:
        datalock.release()
        
      held_timedelta = datetime.datetime.now() - oldestlock[1]
      
      # Check if the oldest lock has been held too long.
      if held_timedelta > MAX_EXPECTED_LOCK_HOLDING_TIMEDELTA:
        message = "Lockserver lock " + str(oldestlock[0])
        message += " has been held since " + str(oldestlock[1])
        message += " (timedelta: " + str(held_timedelta) + ")"
        # Raise an exception which will cause an email to be sent from the
        # except clause below.
        raise InternalError(message)
        
    # Catch all exceptions so that the monitor thread will never die.
    except:
      message = "[monitor_held_lock_times] Something very bad happened: " + traceback.format_exc()
      log.critical(message)
      
      # Send an email to the addresses listed in settings.ADMINS
      if not settings.DEBUG:
        subject = "Critical SeattleGeni lockserver error"
        django.core.mail.mail_admins(subject, message)
        
        # Sleep for 30 minutes to make sure we don't flood the admins with error
        # report emails.
        time.sleep(60 * 30)





def main():

  # Initialize global variables.
  init_globals()

  # Register the XMLRPCServer. Use allow_none to allow allow the python None value.
  server = ThreadedXMLRPCServer(("127.0.0.1", LISTENPORT), allow_none=True)

  log.info("Listening on port " + str(LISTENPORT) + ".")
  
  # Start the background thread that watches for locks being held too long.
  thread.start_new_thread(monitor_held_lock_times, ())

  server.register_instance(LockserverPublicFunctions()) 
  while True:
    server.handle_request()
    # Shutdown the lockserver if there was an internal error.
    # This doesn't actually get detected until another request has been
    # made, as the main server thread is often already blocked in the
    # next handle_request() call when this this value get set.
    if lockserver_had_error:
      sys.exit(1)



if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    log.info("Exiting on KeyboardInterrupt.")
    sys.exit(0)
