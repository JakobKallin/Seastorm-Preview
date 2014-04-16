"""
<Program>
  lockserver_daemon.py

<Started>
  30 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is the XML-RPC Backend that is used by various components of
  SeattleGeni.
 

XML-RPC Interface:
 
 TODO: describe the interface
"""

import datetime
import sys
import time
import traceback

import thread

# These are used to build a single-threaded XMLRPC server.
import SocketServer
import SimpleXMLRPCServer

import xmlrpclib

# To send the admins emails when there's an unhandled exception.
import django.core.mail 

# We use django.db.reset_queries() to prevent memory "leaks" due to query
# logging when settings.DEBUG is True.
import django.db 

# The config module contains the authcode that is required for performing
# privileged operations.
import seattlegeni.backend.config

from seattlegeni.common.api import keydb
from seattlegeni.common.api import keygen
# The lockserver is needed by the vessel cleanup thread.
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb
from seattlegeni.common.api import nodemanager

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import log
from seattlegeni.common.util import parallel

from seattlegeni.common.util.assertions import *

from seattlegeni.common.util.decorators import log_function_call
from seattlegeni.common.util.decorators import log_function_call_without_first_argument

from seattlegeni.website import settings


# The port that we'll listen on.
LISTENPORT = 8020





class ThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  """This is a threaded XMLRPC Server. """
  




def _get_node_handle_from_nodeid(nodeid, owner_pubkey=None):
  
  # Raises DoesNotExistError if no such node exists.
  node = maindb.get_node(nodeid)
  
  # If a specific owner key wasn't provided, use the one that is set in the
  # database for this node.
  if owner_pubkey is None:
    owner_pubkey = node.owner_pubkey
    
  # Raises DoesNotExistError if no such key exists.
  owner_privkey = keydb.get_private_key(owner_pubkey)
  
  return nodemanager.get_node_handle(nodeid, node.last_known_ip, node.last_known_port, owner_pubkey, owner_privkey)

    



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
    Raises InvalidRequestError if args does not contain exact_number
    items.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  if len(args) != exact_number:
    message = "Invalid number of arguments to function " + functionname + ". "
    message += "Expected " + str(exact_number) + ", received " + str(len(args)) + "."
    raise InvalidRequestError(message)





def _assert_valid_authcode(authcode):
  if authcode != seattlegeni.backend.config.authcode:
    raise InvalidRequestError("The provided authcode (" + authcode + ") is invalid.")





class BackendPublicFunctions(object):
  """
  All public functions of this class are automatically exposed as part of the
  xmlrpc interface.
  """
  
  def _dispatch(self, method, args):
    """
    We provide a _dispatch function (which SimpleXMLRPCServer looks for and
    uses) so that we can log exceptions due to our programming errors within
    the backend as well to detect incorrect usage by clients.
    """
      
    try:
      # Get the requested function (making sure it exists).
      try:
        func = getattr(self, method)
      except AttributeError:
        raise InvalidRequestError("The requested method '" + method + "' doesn't exist.")
      
      # Call the requested function.
      return func(*args)
    
    except NodemanagerCommunicationError, e:
      raise xmlrpclib.Fault(100, "Node communication failure: " + str(e))
    
    except (DoesNotExistError, InvalidRequestError, AssertionError):
      log.error("The backend was used incorrectly: " + traceback.format_exc())
      raise
    
    except:
      # We assume all other exceptions are bugs in the backend. Unlike the
      # lockserver where it might result in broader data corruption, here in
      # the backend we allow the backend to continue serving other requests.
      # That is, we don't go through steps to try to shutdown the backend.
      
      message = "The backend had an internal error: " + traceback.format_exc()
      log.critical(message)
      
      # Send an email to the addresses listed in settings.ADMINS
      if not settings.DEBUG:
        subject = "Critical SeattleGeni backend error"
        django.core.mail.mail_admins(subject, message)
      
      raise
      




  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  @log_function_call
  def GenerateKey(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('GenerateKey', args, 1)
    
    keydescription = args[0]
    
    assert_str(keydescription)
    
    # Generate a new keypair.
    (pubkey, privkey) = keygen.generate_keypair()
    
    # Store the private key in the keydb.
    keydb.set_private_key(pubkey, privkey, keydescription)
    
    # Return the public key as a string.
    return pubkey





  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  @log_function_call
  def SetVesselUsers(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('SetVesselUsers', args, 3)
    (nodeid, vesselname, userkeylist) = args
    
    assert_str(nodeid)
    assert_str(vesselname)
    assert_list(userkeylist)
    
    for userkey in userkeylist:
      assert_str(userkey)

    # Note: The nodemanager checks whether each key is a valid key and will
    #       raise an exception if it is not.
      
    # Raises a DoesNotExistError if there is no node with this nodeid.
    nodehandle = _get_node_handle_from_nodeid(nodeid)
    
    # Raises NodemanagerCommunicationError if it fails.
    nodemanager.change_users(nodehandle, vesselname, userkeylist)





  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  @log_function_call_without_first_argument
  def SetVesselOwner(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('SetVesselOwner', args, 5)
    (authcode, nodeid, vesselname, old_ownerkey, new_ownerkey) = args
    
    assert_str(authcode)
    assert_str(nodeid)
    assert_str(vesselname)
    assert_str(old_ownerkey)
    assert_str(new_ownerkey)
    
    _assert_valid_authcode(authcode)
    
    # Note: The nodemanager checks whether the owner key is a valid key and
    #       will raise an exception if it is not.
    
    # Raises a DoesNotExistError if there is no node with this nodeid.
    nodehandle = _get_node_handle_from_nodeid(nodeid, owner_pubkey=old_ownerkey)
    
    # Raises NodemanagerCommunicationError if it fails.
    nodemanager.change_owner(nodehandle, vesselname, new_ownerkey)
    
    
    
 
    
  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  @log_function_call_without_first_argument
  def SplitVessel(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('SplitVessels', args, 4)
    (authcode, nodeid, vesselname, desiredresourcedata) = args
    
    assert_str(authcode)
    assert_str(nodeid)
    assert_str(vesselname)
    assert_str(desiredresourcedata)
    
    _assert_valid_authcode(authcode)
    
    # Raises a DoesNotExistError if there is no node with this nodeid.
    nodehandle = _get_node_handle_from_nodeid(nodeid)
    
    # Raises NodemanagerCommunicationError if it fails.
    return nodemanager.split_vessel(nodehandle, vesselname, desiredresourcedata)
    
    



  # Using @staticmethod makes it so that 'self' doesn't get passed in as the first arg.
  @staticmethod
  @log_function_call_without_first_argument
  def JoinVessels(*args):
    """
    This is a public function of the XMLRPC server. See the module comments at
    the top of the file for a description of how it is used.
    """
    _assert_number_of_arguments('JoinVessels', args, 4)
    (authcode, nodeid, firstvesselname, secondvesselname) = args
    
    assert_str(authcode)
    assert_str(nodeid)
    assert_str(firstvesselname)
    assert_str(secondvesselname)
    
    _assert_valid_authcode(authcode)
    
    # Raises a DoesNotExistError if there is no node with this nodeid.
    nodehandle = _get_node_handle_from_nodeid(nodeid)
    
    # Raises NodemanagerCommunicationError if it fails.
    return nodemanager.join_vessels(nodehandle, firstvesselname, secondvesselname)
      




def cleanup_vessels():
  """
  This function is started as separate thread. It continually checks whether
  there are vessels needing to be cleaned up and initiates cleanup as needed.
  """
  
  log.info("[cleanup_vessels] cleanup thread started.")

  # Start a transaction management.
  django.db.transaction.enter_transaction_management()

  # Run forever.
  while True:
    
    try:
      
      # Sleep a few seconds for those times where we don't have any vessels to clean up.
      time.sleep(5)
      
      # We shouldn't be running the backend in production with
      # settings.DEBUG = True. Just in case, though, tell django to reset its
      # list of saved queries each time through the loop. Note that this is not
      # specific to the cleanup thread as other parts of the backend are using
      # the maindb, as well, so we're overloading the purpose of the cleanup
      # thread by doing this here. This is just a convenient place to do it.
      # See http://docs.djangoproject.com/en/dev/faq/models/#why-is-django-leaking-memory
      # for more info.
      if settings.DEBUG:
        django.db.reset_queries()
      
      # First, make it so that expired vessels are seen as dirty. We aren't
      # holding a lock on the nodes when we do this. It's possible that we do
      # this while someone else has a lock on the node. What would result?
      # I believe the worst result is that a user has their vessel marked as
      # dirty after they renewed in the case where they are renewing it just
      # as it expires (with some exceptionally bad timing involved). And, 
      # that's not really very bad as if the user is trying to renew at the
      # exact moment it expires, their trying their luck with how fast their
      # request gets processed, anyways. In short, I don't think it's important
      # enough to either obtain locks to do this or to rewrite the code to
      # avoid any need for separately marking expired vessels as dirty rather
      # than just trying to process expired vessels directly in the code below.
      date_started=datetime.datetime.now()
      expired_list = maindb.mark_expired_vessels_as_dirty()
      if len(expired_list) > 0:
        log.info("[cleanup_vessels] " + str(len(expired_list)) + 
                 " expired vessels have been marked as dirty: " + str(expired_list))
        maindb.create_action_log_event("mark_expired_vessels_as_dirty", user=None, second_arg=None,
                                       third_arg=None, was_successful=True, message=None,
                                       date_started=date_started, vessel_list=expired_list)

      # Get a list of vessels to clean up. This doesn't include nodes known to
      # be inactive as we would just continue failing to communicate with nodes
      # that are down.
      cleanupvessellist = maindb.get_vessels_needing_cleanup()
      if len(cleanupvessellist) == 0:
        continue
        
      log.info("[cleanup_vessels] " + str(len(cleanupvessellist)) + " vessels to clean up: " + str(cleanupvessellist))
      
      parallel_results = parallel.run_parallelized(cleanupvessellist, _cleanup_single_vessel)
        
      if len(parallel_results["exception"]) > 0:
        for vessel, exception_message in parallel_results["exception"]:
          log_message = "Unhandled exception during parallelized vessel cleanup: " + exception_message
          log.critical(log_message)
        # Raise the last exceptions so that the admin gets an email.
        raise InternalError(log_message)  
    
    except:
      message = "[cleanup_vessels] Something very bad happened: " + traceback.format_exc()
      log.critical(message)
      
      # Send an email to the addresses listed in settings.ADMINS
      if not settings.DEBUG:
        subject = "Critical SeattleGeni backend error"
        django.core.mail.mail_admins(subject, message)
        
        # Sleep for ten minutes to make sure we don't flood the admins with error
        # report emails.
        time.sleep(600)
    finally:
      # Manually commit the transaction to prevent caching.
      django.db.transaction.commit()
      




def _cleanup_single_vessel(vessel):
  """
  This function is passed by cleanup_vessels() as the function argument to
  run_parallelized().
  """
  
  # This does seem wasteful of lockserver communication to require four
  # round-trips with the lockserver (get handle, lock, unlock, release handle),
  # but if we really want to fix that then I think the best thing to do would
  # be to allow obtaining a lockhandle and releasing a lockhandle to be done
  # in the same calls as lock acquisition and release. 
  
  node_id = maindb.get_node_identifier_from_vessel(vessel)
  lockserver_handle = lockserver.create_lockserver_handle()
  
  # Lock the node that the vessels is on.
  lockserver.lock_node(lockserver_handle, node_id)
  try:
    # Get a new vessel object from the db in case it was modified in the db
    # before the lock was obtained.
    vessel = maindb.get_vessel(node_id, vessel.name)
    
    # Now that we have a lock on the node that this vessel is on, find out
    # if we should still clean up this vessel (e.g. maybe a node state
    # transition script moved the node to a new state and this vessel was
    # removed).
    needscleanup, reasonwhynot = maindb.does_vessel_need_cleanup(vessel)
    if not needscleanup:
      log.info("[_cleanup_single_vessel] Vessel " + str(vessel) + 
               " no longer needs cleanup: " + reasonwhynot)
      return
    
    nodeid = maindb.get_node_identifier_from_vessel(vessel)
    nodehandle = _get_node_handle_from_nodeid(nodeid)
    
    try:
      log.info("[_cleanup_single_vessel] About to ChangeUsers on vessel " + str(vessel))
      nodemanager.change_users(nodehandle, vessel.name, [''])
      log.info("[_cleanup_single_vessel] About to ResetVessel on vessel " + str(vessel))
      nodemanager.reset_vessel(nodehandle, vessel.name)
    except NodemanagerCommunicationError:
      # We don't pass this exception up. Maybe the node is offline now. At some
      # point, it will be marked in the database as offline (should we be doing
      # that here?). At that time, the dirty vessels on that node will not be
      # in the cleanup list anymore.
      log.info("[_cleanup_single_vessel] Failed to cleanup vessel " + 
               str(vessel) + ". " + traceback.format_exc())
      return
      
    # We only mark it as clean if no exception was raised when trying to
    # perform the above nodemanager operations.
    maindb.mark_vessel_as_clean(vessel)
  
    log.info("[_cleanup_single_vessel] Successfully cleaned up vessel " + str(vessel))

  finally:
    # Unlock the node.
    lockserver.unlock_node(lockserver_handle, node_id)
    lockserver.destroy_lockserver_handle(lockserver_handle)





def sync_user_keys_of_vessels():
  """
  This function is started as separate thread. It continually checks whether
  there are vessels needing their user keys sync'd and initiates the user key
  sync as needed.
  """

  log.info("[sync_user_keys_of_vessels] thread started.")

  # Run forever.
  while True:
    
    try:
      
      # Sleep a few seconds for those times where we don't have any vessels to clean up.
      time.sleep(5)
      
      # We shouldn't be running the backend in production with
      # settings.DEBUG = True. Just in case, though, tell django to reset its
      # list of saved queries each time through the loop.
      if settings.DEBUG:
        django.db.reset_queries()
      
      # Get a list of vessels that need to have user keys sync'd. This doesn't
      # include nodes known to be inactive as we would just continue failing to
      # communicate with nodes that are down.
      vessellist = maindb.get_vessels_needing_user_key_sync()
      if len(vessellist) == 0:
        continue
        
      log.info("[sync_user_keys_of_vessels] " + str(len(vessellist)) + 
               " vessels to have user keys sync'd: " + str(vessellist))
     
      parallel_results = parallel.run_parallelized(vessellist, _sync_user_keys_of_single_vessel)
     
      if len(parallel_results["exception"]) > 0:
        for vessel, exception_message in parallel_results["exception"]:
          log_message = "Unhandled exception during parallelized vessel user key sync: " + exception_message
          log.critical(log_message)
        # Raise the last exceptions so that the admin gets an email.
        raise InternalError(log_message)
        
    except:
      message = "[sync_user_keys_of_vessels] Something very bad happened: " + traceback.format_exc()
      log.critical(message)
      
      # Send an email to the addresses listed in settings.ADMINS
      if not settings.DEBUG:
        subject = "Critical SeattleGeni backend error"
        django.core.mail.mail_admins(subject, message)
        
        # Sleep for ten minutes to make sure we don't flood the admins with error
        # report emails.
        time.sleep(600)





def _sync_user_keys_of_single_vessel(vessel):
  """
  This function is passed by sync_user_keys_of_vessels() as the function
  argument to run_parallelized().
  """
  
  # This does seem wasteful of lockserver communication to require four
  # round-trips with the lockserver (get handle, lock, unlock, release handle),
  # but if we really want to fix that then I think the best thing to do would
  # be to allow obtaining a lockhandle and releasing a lockhandle to be done
  # in the same calls as lock acquisition and release. 
  
  node_id = maindb.get_node_identifier_from_vessel(vessel)
  lockserver_handle = lockserver.create_lockserver_handle()
  
  # Lock the node that the vessels is on.
  lockserver.lock_node(lockserver_handle, node_id)
  try:
    # Get a new vessel object from the db in case it was modified in the db
    # before the lock was obtained.
    vessel = maindb.get_vessel(node_id, vessel.name)
  
    # Now that we have a lock on the node that this vessel is on, find out
    # if we should still sync user keys on this vessel (e.g. maybe a node state
    # transition script moved the node to a new state and this vessel was
    # removed).
    needssync, reasonwhynot = maindb.does_vessel_need_user_key_sync(vessel)
    if not needssync:
      log.info("[_sync_user_keys_of_single_vessel] Vessel " + str(vessel) + 
               " no longer needs user key sync: " + reasonwhynot)
      return
    
    nodeid = maindb.get_node_identifier_from_vessel(vessel)
    nodehandle = _get_node_handle_from_nodeid(nodeid)
    
    # The list returned from get_users_with_access_to_vessel includes the key of
    # the user who has acquired the vessel along with any other users they have
    # given access to.
    user_list = maindb.get_users_with_access_to_vessel(vessel)
    
    key_list = []
    for user in user_list:
      key_list.append(user.user_pubkey)
      
    if len(key_list) == 0:
      raise InternalError("InternalError: Empty user key list for vessel " + str(vessel))
    
    try:
      log.info("[_sync_user_keys_of_single_vessel] About to ChangeUsers on vessel " + str(vessel))
      nodemanager.change_users(nodehandle, vessel.name, key_list)
    except NodemanagerCommunicationError:
      # We don't pass this exception up. Maybe the node is offline now. At some
      # point, it will be marked in the database as offline and won't show up in
      # our list of vessels to sync user keys of anymore.
      log.info("[_sync_user_keys_of_single_vessel] Failed to sync user keys of vessel " + 
               str(vessel) + ". " + traceback.format_exc())
      return
      
    # We only mark it as sync'd if no exception was raised when trying to perform
    # the above nodemanager operations.
    maindb.mark_vessel_as_not_needing_user_key_sync(vessel)
  
    log.info("[_sync_user_keys_of_single_vessel] Successfully sync'd user keys of vessel " + str(vessel))

  finally:
    # Unlock the node.
    lockserver.unlock_node(lockserver_handle, node_id)
    lockserver.destroy_lockserver_handle(lockserver_handle)





def main():
  
  # Initialize the main database.
  maindb.init_maindb()

  # Initialize the key database.
  keydb.init_keydb()
  
  # Initialize the nodemanager.
  nodemanager.init_nodemanager()

  # Start the background thread that does vessel cleanup.
  thread.start_new_thread(cleanup_vessels, ())
  
  # Start the background thread that does vessel user key synchronization.
  thread.start_new_thread(sync_user_keys_of_vessels, ())
  
  # Register the XMLRPCServer. Use allow_none to allow allow the python None value.
  server = ThreadedXMLRPCServer(("127.0.0.1", LISTENPORT), allow_none=True)

  log.info("Backend listening on port " + str(LISTENPORT) + ".")

  server.register_instance(BackendPublicFunctions()) 
  while True:
    server.handle_request()





if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    log.info("Exiting on KeyboardInterrupt.")
    sys.exit(0)
