"""
<Program>
  lockserver.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is the API that should be used to interact with the Lockserver.
  Functions in this module are the only way that other code should interact
  with the Lockserver.
   
  There is no provided function to unlock both user locks and node lock
  in a single call even though that is currently supported by the Lockserver.
  This can be added later, if needed.

  There are separate calls for locking/unlocking a single user or node
  and locking/unlocking multiple users or nodes. This is to make client
  code easier to read and less error-prone (e.g. forgetting to pass a
  list that contains a single name and instead directly passing the
  string that has the lock name).

  For details about the locking rules, see the module comments in
  lockserver_daemon.py.


<Usage>
  # Create a lockserver handle.
  lockserver_handle = create_lockserver_handle()

  # Lock request blocks until lock is obtained.
  lock_user(lockserver_handle, 'bob')

  # Release the user lock in a finally block.
  try:
    ...
    # Lock request blocks until lock is obtained.
    lock_multiple_nodes(lockserver_handle, ['123', '456'])
  
    # Release the node locks in a finally block.
    try:
      ...
    
    finally:
      # Unlock requests do not block.
      unlock_multiple_nodes(lockserver_handle, ['123', '456'])

  finally:
    # If unlock_user threw an exception here, we wouldn't destroy the lockserver
    # handle. That is not good, but it's not the critical error that failing to
    # release the user lock would be.
    unlock_user(lockserver_handle, 'bob')
  
    # Destroy the lockserver handle (don't forget to do this!)
    destroy_lockserver_handle(lockserver_handle)

"""

import datetime
import socket
import traceback
import xmlrpclib

from seattlegeni.common.exceptions import *

from seattlegeni.common.util.decorators import log_function_call





# The default lockserver url to use.
LOCKSERVER_URL = "http://127.0.0.1:8010"

# Constants to prevent unnoticed typos in the code below.
REQUEST_TYPE_LOCK = 'lock'
REQUEST_TYPE_UNLOCK = 'unlock'





@log_function_call
def create_lockserver_handle(lockserver_url=LOCKSERVER_URL):
  """
  <Purpose>
    Create a handle for communication with a lockserver. This is a required
    step before a client calls any of the (un)lock_* functions in this module.
    Note that a client should only create a single handle across multiple
    lock requests. This may require passing the handle around in function calls
    so that helper functions that create locks can use the same handle.
    It is very important that the lockserver handle be later destroyed by
    calling destroy_lockserver_handle().
  <Arguments>
    lockserver_url
      The url of the lockserver. Defaults to the lockserver running locally on
      its usual port.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Starts a session with the lockserver.
  <Returns>
    A lockserver handle.
  """
  
  lockserver_handle = {}
  lockserver_handle["proxy"] = xmlrpclib.ServerProxy(lockserver_url)
  
  try:
    lockserver_handle["session_id"] = lockserver_handle["proxy"].StartSession()
  except xmlrpclib.Fault:
    raise ProgrammerError("The lockserver rejected the request: " + traceback.format_exc())
  except xmlrpclib.ProtocolError:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
  except socket.error:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
  
  return lockserver_handle





def destroy_lockserver_handle(lockserver_handle):
  """
  <Purpose>
    Destroys a lockserver handle previously created with
    create_lockserver_handle().
  <Arguments>
    lockserver_handle
      The lockserver handle to destroy.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Ends the session on the lockserver.
  <Returns>
    None.
  """
  
  try:
    lockserver_handle["proxy"].EndSession(lockserver_handle["session_id"])
  except xmlrpclib.Fault:
    raise ProgrammerError("The lockserver rejected the request: " + traceback.format_exc())
  except xmlrpclib.ProtocolError:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
  except socket.error:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())





def lock_user(lockserver_handle, username):
  """
  <Purpose>
    Obtains a user lock.
  <Arguments>
    lockserver_handle
      The lockserver handle whose session the lock will be obtained under.
    username
      The username string of the user to obtain the lock on.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Blocks until the lock is obtained.
  <Returns>
    None.
  """
  _perform_lock_request(REQUEST_TYPE_LOCK, lockserver_handle, user_list=[username])





def unlock_user(lockserver_handle, username):
  """
  <Purpose>
    Release a user lock previously obtained with the same lockserver_handle.
  <Arguments>
    lockserver_handle
      The lockserver handle whose session the lock will be released under.
    username
      The username string of the user to release the lock of.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Releases the lock.
  <Returns>
    None.
  """
  _perform_lock_request(REQUEST_TYPE_UNLOCK, lockserver_handle, user_list=[username])





def lock_multiple_users(lockserver_handle, username_list):
  """
  <Purpose>
    Obtains locks on multiple users.
  <Arguments>
    lockserver_handle
      The lockserver handle whose session the locks will be obtained under.
    username_list
      The list of username strings of the users to obtain locks on.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Blocks until all requested locks are obtained.
  <Returns>
    None.
  """
  _perform_lock_request(REQUEST_TYPE_LOCK, lockserver_handle, user_list=username_list)





def unlock_multiple_users(lockserver_handle, username_list):
  """
  <Purpose>
    Release user locks previously obtained with the same lockserver_handle.
  <Arguments>
    lockserver_handle
      The lockserver handle whose session the locks will be released under.
    username_list
      The list of username strings of the users to release the locks of.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    Releases the locks.
  <Returns>
    None.
  """
  _perform_lock_request(REQUEST_TYPE_UNLOCK, lockserver_handle, user_list=username_list)





def lock_node(lockserver_handle, node_id):
  """
  See the comments for the user lock functions as well as the locking rules
  described in the module comments.
  """
  _perform_lock_request(REQUEST_TYPE_LOCK, lockserver_handle, node_list=[node_id])





def unlock_node(lockserver_handle, node_id):
  """
  See the comments for the user lock functions as well as the locking rules
  described in the module comments.
  """
  _perform_lock_request(REQUEST_TYPE_UNLOCK, lockserver_handle, node_list=[node_id])





def lock_multiple_nodes(lockserver_handle, node_id_list):
  """
  See the comments for the user lock functions as well as the locking rules
  described in the module comments.
  """
  _perform_lock_request(REQUEST_TYPE_LOCK, lockserver_handle, node_list=node_id_list)





def unlock_multiple_nodes(lockserver_handle, node_id_list):
  """
  See the comments for the user lock functions as well as the locking rules
  described in the module comments.
  """
  _perform_lock_request(REQUEST_TYPE_UNLOCK, lockserver_handle, node_list=node_id_list)



  
  
def _perform_lock_request(request_type, lockserver_handle, user_list=None, node_list=None):
  """
  A helper function that does the actual lock or unlock calls to the lockserver.
  """

  session_id = lockserver_handle["session_id"]
  lockdict = {}
  
  if user_list is not None:
    lockdict["user"] = user_list
  if node_list is not None:
    lockdict["node"] = node_list
  
  if request_type is REQUEST_TYPE_LOCK:
    request_func = lockserver_handle["proxy"].AcquireLocks
  elif request_type is REQUEST_TYPE_UNLOCK:
    request_func = lockserver_handle["proxy"].ReleaseLocks
  else:
    raise ProgrammerError("Invalid lock request type specified: " + str(request_type))
    
  try:
    request_func(session_id, lockdict)
  except xmlrpclib.Fault:
    raise ProgrammerError("The lockserver rejected the request: " + traceback.format_exc())
  except xmlrpclib.ProtocolError:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
  except socket.error:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())





def get_status(lockserver_url=LOCKSERVER_URL):
  """
  <Purpose>
    Query the lockserver for its status. This function is for monitoring
    purposes and will never need to be called during normal operation.
  <Arguments>
    lockserver_url
      The url of the lockserver to call GetStatus on. Defaults to LOCKSERVER_URL.
  <Exceptions>
    ProgrammerError
    InternalError
      If the lockserver can't be communicated with.
  <Side Effects>
    None
  <Returns>
    See the documentation for the GetStatus() call in lockserver_daemon.py.
  """
  
  proxy = xmlrpclib.ServerProxy(lockserver_url)
  try:
    statusdict = proxy.GetStatus()
    
    # Convert the locktimelist datetime object string representations back into
    # datetime objects. Code borrowed from:
    # http://docs.python.org/library/xmlrpclib.html#datetime-objects
    locktimelist = []
    for locktimeitem in statusdict["locktimelist"]:
      # Convert the ISO8601 string to a datetime object.
      print locktimeitem[1].value
      converteddatetime = datetime.datetime.strptime(locktimeitem[1].value, "%Y%m%dT%H:%M:%S")
      locktimelist.append((locktimeitem[0], converteddatetime))
    statusdict["locktimelist"] = locktimelist
    
    return statusdict

  except xmlrpclib.Fault:
    raise ProgrammerError("The lockserver rejected the request: " + traceback.format_exc())
  except xmlrpclib.ProtocolError:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
  except socket.error:
    raise InternalError("Unable to communicate with the lockserver: " + traceback.format_exc())
    
