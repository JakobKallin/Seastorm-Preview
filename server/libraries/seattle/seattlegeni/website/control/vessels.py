"""
<Program Name>
  vessels.py

<Started>
  July 16, 2009

<Author>
  Justin Samuel

<Purpose>
  Provides utilities for the controller interface (interface.py) to use for
  performing acquisition of different types of vessels as well as release of
  vessels.
"""

import traceback

from seattlegeni.common.exceptions import *

from seattlegeni.common.api import backend
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb

from seattlegeni.common.util import log
from seattlegeni.common.util import parallel

from seattlegeni.common.util.decorators import log_function_call





@log_function_call
def _parallel_process_vessels_from_list(vessel_list, process_func, lockserver_handle, *args):
  """
  Obtain locks on all of the nodes of vessels in vessel_list, get fresh vessel
  objects from the databae, and then parallelize a call to process_func to
  process each vessel in vessel_list (passing the additional *args to
  process_func).
  """
  
  node_id_list = []
  for vessel in vessel_list:
    node_id = maindb.get_node_identifier_from_vessel(vessel)
    # Lock names must be unique, and there could be multiple vessels from the
    # same node in the vessel_list.
    if node_id not in node_id_list:
      node_id_list.append(node_id)

  # Lock the nodes that these vessels are on.
  lockserver.lock_multiple_nodes(lockserver_handle, node_id_list)
  try:
    # Get new vessel objects from the db now that we have node locks.
    new_vessel_list = []
    for vessel in vessel_list:
      node_id = maindb.get_node_identifier_from_vessel(vessel)
      new_vessel_list.append(maindb.get_vessel(node_id, vessel.name))
    # Have the list object the caller may still be using contain the actual
    # vessel objects we have processed. That is, we've just replaced the
    # caller's list's contents with new vessel objects for the same vessels.
    vessel_list[:] = new_vessel_list[:]
  
    return parallel.run_parallelized(vessel_list, process_func, *args)
    
  finally:
    # Unlock the nodes.
    lockserver.unlock_multiple_nodes(lockserver_handle, node_id_list)





@log_function_call
def acquire_specific_vessels_best_effort(lockserver_handle, geniuser, vessel_list):
  """
  <Purpose>
    Acquire for geniuser as many vessels in vessel_list as possible.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vessel_list
      The vessels to attempt to acquire for geniuser.
  <Exceptions>
    None
  <Side Effects>
    Zero or more of the vessels are acquired for the user. The database has
    been updated to reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  acquired_vessels = []
  
  parallel_results = _parallel_process_vessels_from_list(vessel_list, _do_acquire_vessel,
                                                         lockserver_handle, geniuser)

  # The "exception" key contains a list of tuples where the first item of
  # the tuple is the vessel object and the second item is the str(e) of
  # the exception. Because the repy parellelization module that is used
  # underneath only passes up the exception string, we have made
  # _do_acquire_vessel() include the string "UnableToAcquireResourcesError"
  # in the exception message so we can tell these apart from more
  # serious failures (e.g the backed is down).
  for (vessel, exception_message) in parallel_results["exception"]:
    
    if "UnableToAcquireResourcesError" in exception_message:
      # This is ok, maybe the node is offline.
      log.info("Failed to acquire vessel: " + str(vessel))
      
    elif "UnableToAcquireResourcesError" not in exception_message:
      # Something serious happened, maybe the backend is down.
      raise InternalError("Unexpected exception occurred during parallelized " + 
                          "acquisition of vessels: " + exception_message)
    
  # The "returned" key contains a list of tuples where the first item of
  # the tuple is the vessel object and the second is the return value
  # (which is None).
  for (ignored_argument_vessel, returned_vessel) in parallel_results["returned"]:
    # We successfully acquired this vessel.
    # Append the returned vessel from _do_acquire_vessel() rather than
    # the argument that the parallelize.repy library used. Somewhere
    # along the way a copy of the argument_vessel is being made so it
    # doesn't reflect changes made to it.
    acquired_vessels.append(returned_vessel)

  return acquired_vessels





@log_function_call
def acquire_wan_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'wan' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list of vessels where no two vessels are on the same subnet.
  vessel_list = maindb.get_available_wan_vessels(geniuser, vesselcount)
  
  return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)





@log_function_call
def acquire_nat_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'nat' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list of nat vessels.
  vessel_list = maindb.get_available_nat_vessels(geniuser, vesselcount)
  
  return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)





@log_function_call
def acquire_lan_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'lan' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list that itself contains lists of vessels on the same subnet.
  subnet_vessel_list = maindb.get_available_lan_vessels_by_subnet(geniuser, vesselcount)
  
  # This case is a little more involved than with wan or rand vessels. If we
  # fail to get the number of desired vessels from one subnet, we need to try
  # another until we are out of subnets to try.
  for vessel_list in subnet_vessel_list:
    try:
      # If we don't hit an exception and return, then we found a subnet where
      # we could acquire all of the requested vessels. So, we're done.
      return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)
    except UnableToAcquireResourcesError:
      # Try the next subnet.
      continue

  # If we made it here, we tried all subnets in our list.
  raise UnableToAcquireResourcesError





@log_function_call
def acquire_rand_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'rand' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list of vessels where there are no guarantees about whether
  # the list includes wan vessels, lan vessels, vessels on the same subnet, etc.
  vessel_list = maindb.get_available_rand_vessels(geniuser, vesselcount)
  
  return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)





@log_function_call
def _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list):
  """
  This function will try to acquire vesselcount vessels from vessel_list.
  If less than vesselcount can be acquired, then the partial set of
  vessels that were acquired will be released by this function before it
  returns.
  
  Returns the list of acquired vessels if successful.
  """
  
  # Make sure there are sufficient vessels to even try to fulfill the request.
  if len(vessel_list) < vesselcount:
    raise UnableToAcquireResourcesError("There are not enough available vessels to fulfill the request.")
  
  acquired_vessels = []

  remaining_vessel_list = vessel_list[:]

  # Keep trying to acquire vessels until there are no more left to acquire.
  # There's a "return" statement in the loop that will get out of the loop
  # once we've obtained all of the vessels we wanted, so here we are only
  # concerned with there being any vessels left to try.
  while len(remaining_vessel_list) > 0:
  
    # Each time through the loop we'll try to acquire the number of vessels
    # remaining that are needed to fulfill the user's request.
    remaining_needed_vesselcount = vesselcount - len(acquired_vessels)
    next_vessels_to_acquire = remaining_vessel_list[:remaining_needed_vesselcount]
    remaining_vessel_list = remaining_vessel_list[remaining_needed_vesselcount:]
  
    # Note that we haven't worried about checking if the number of remaining
    # vessels could still fulfill the user's request. In the name of
    # correctness over efficiency, we'll let this case that should be rare
    # (at least until the vesselcount's users are request get to be huge)
    # sort itself out with a few unnecessary vessel acquisition before they
    # ultimately get released after this loop.
  
    parallel_results = _parallel_process_vessels_from_list(next_vessels_to_acquire, _do_acquire_vessel,
                                                           lockserver_handle, geniuser)
  
    # The "exception" key contains a list of tuples where the first item of
    # the tuple is the vessel object and the second item is the str(e) of
    # the exception. Because the repy parellelization module that is used
    # underneath only passes up the exception string, we have made
    # _do_acquire_vessel() include the string "UnableToAcquireResourcesError"
    # in the exception message so we can tell these apart from more
    # serious failures (e.g the backed is down).
    for (vessel, exception_message) in parallel_results["exception"]:
      
      if "UnableToAcquireResourcesError" in exception_message:
        # This is ok, maybe the node is offline.
        log.info("Failed to acquire vessel: " + str(vessel))
        
      elif "UnableToAcquireResourcesError" not in exception_message:
        # Something serious happened, maybe the backend is down.
        raise InternalError("Unexpected exception occurred during parallelized " + 
                            "acquisition of vessels: " + exception_message)
    
    # The "returned" key contains a list of tuples where the first item of
    # the tuple is the vessel object and the second is the return value
    # (which is None).
    for (ignored_argument_vessel, returned_vessel) in parallel_results["returned"]:
      # We successfully acquired this vessel.
      # Append the returned vessel from _do_acquire_vessel() rather than
      # the argument that the parallelize.repy library used. Somewhere
      # along the way a copy of the argument_vessel is being made so it
      # doesn't reflect changes made to it.
      acquired_vessels.append(returned_vessel)

    # If we've acquired all of the vessels the user wanted, we're done.
    if len(acquired_vessels) == vesselcount:
      log.info("Successfully acquired vessel: " + str(returned_vessel))
      return acquired_vessels

  # If we got here, then we didn't acquire the vessels the user wanted. We
  # release any vessels that may have been acquired rather than leave the user
  # with a partial set of what they requested.
  if acquired_vessels:
    release_vessels(lockserver_handle, geniuser, acquired_vessels)

  raise UnableToAcquireResourcesError("Failed to acquire enough vessels to fulfill the request")





@log_function_call
def _do_acquire_vessel(vessel, geniuser):
  """
  Perform that actual acquisition of the vessel by the user (through the
  backend) and update the database accordingly if the vessel is successfully
  acquired.
  
  This gets called parallelized after a node lock is already obtained for the
  vessel.

  When an UnableToAcquireResourcesError is raised, the exception message
  will contain the string "UnableToAcquireResourcesError" so that it can be
  seen in the results of a call to repy's parallelization function.  
  """
  
  node_id = maindb.get_node_identifier_from_vessel(vessel)
  
  if vessel.acquired_by_user is not None:
    message = "Vessel already acquired once the node lock was obtained."
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + message)
  
  node = maindb.get_node(node_id)
  if node.is_active is False:
    message = "Vessel's node is no longer active once the node lock was obtained."
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + message)
  
  # This will raise a UnableToAcquireResourcesException if it fails (e.g if
  # the node is down). We want to allow the exception to be passed up to
  # the caller.
  try:
    backend.acquire_vessel(geniuser, vessel)
  except UnableToAcquireResourcesError, e:
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + str(e))
  
  # Update the database to reflect the successful vessel acquisition.
  maindb.record_acquired_vessel(geniuser, vessel)
    
  # The _acquire_vessels_from_list() function will make use of this return value.
  return vessel





@log_function_call
def flag_vessels_for_user_keys_sync(lockserver_handle, vessel_list):
  """
  This function will mark (flag) the vessels in vessel_list as needing
  their user keys synced. The backend will then notice the vessels flagged
  in this way and will sync the user keys.
  
  We don't try to do the actual updating of user keys on vessels as that seems
  like a bad user experience, especially down the road when we may allow the
  users some form of giving others access to their vessels. Imagine a user wants
  to add ten users to their 300 acquired vessels and every time they add one
  of the users they have to wait minutes for keys to be update on vessels, and
  then we still get stuck having to deal with the case of temporary failures
  in communication and needing to go back and update some vessels later.
  
  <Returns>
    None
  """
  
  # This is going to be a potentially large list of vessels to obtain node
  # locks on simultaneously. This is something to revisit if lock contention
  # starts to become an issue.
  parallel_results = _parallel_process_vessels_from_list(vessel_list, _do_flag_vessels_for_user_keys_sync,
                                                         lockserver_handle)
  
  for (vessel, exception_message) in parallel_results["exception"]:
    raise InternalError("Unexpected exception occurred during parallelized " + 
                        "vessel user key out-of-sync flagging: " + exception_message)
  




@log_function_call
def _do_flag_vessels_for_user_keys_sync(vessel):
  """
  Indicates in the database that the vessel needs its user keys sync'd. This
  gets called parallelized after a node lock is already obtained for the
  vessel.
  """
  
  maindb.mark_vessel_as_needing_user_key_sync(vessel)





@log_function_call
def release_vessels(lockserver_handle, geniuser, vessel_list):
  """
  <Purpose>
    Release vessels (regardless of which user has acquired them)
  <Arguments>
    lockserver_handle
      The lockserver handle to use for acquiring node locks.
    geniuser
      The geniuser that has acquired the vessels to be released.
    vessel_list
      A list of vessels to be released.
  <Exceptions>
    None.
  <Side Effects>
    The vessels in the vessel_list are released.
  <Returns>
    None.
  """
    
  # This is going to be a potentially large list of vessels to obtain node
  # locks on simultaneously. This is something to revisit if lock contention
  # starts to become an issue.
  parallel_results = _parallel_process_vessels_from_list(vessel_list, _do_release_vessel,
                                                         lockserver_handle, geniuser)
  
  for (vessel, exception_message) in parallel_results["exception"]:
      raise InternalError("Unexpected exception occurred during parallelized " + 
                          "release of vessels: " + exception_message)

    



@log_function_call
def _do_release_vessel(vessel, geniuser):
  """
  Obtains a lock on the node the vessel is on and then makes a call to the
  backend to release the vessel.
  """
  
  if vessel.acquired_by_user != geniuser:
    # The vessel was either already released, someone is trying to do things
    # they shouldn't, or we have a bug.
    log.info("Not releasing vessel " + str(vessel) + 
             " because it is not acquired by user " + str(geniuser))
    return
  
  # We don't check for node.is_active == True because we might as well have
  # the backend try to clean up the vessel even if the database says it's
  # inactive (maybe the node is back online?).
  
  # This will not raise an exception, even if the node the vessel is on is down.
  backend.release_vessel(vessel)
  
  # Update the database to reflect the release of the vessel.
  maindb.record_released_vessel(vessel)





@log_function_call
def renew_vessels(lockserver_handle, geniuser, vessel_list):
  """
  <Purpose>
    Renew vessels.
  <Arguments>
    lockserver_handle
      The lockserver handle to use for acquiring node locks.
    geniuser
      The user who has acquired the vessels.
    vessel_list
      A list of vessels to be renewed.
  <Exceptions>
    InvalidRequestError
      If any vessels in vessel_list are not already acquired by geniuser.
  <Side Effects>
    The vessels in the vessel_list have expirations dates which are the maximum
    length of time from now that we allow renewal for.
  <Returns>
    None.
  """
  
  # This is going to be a potentially large list of vessels to obtain node
  # locks on simultaneously. This is something to revisit if lock contention
  # starts to become an issue.
  parallel_results = _parallel_process_vessels_from_list(vessel_list, _do_renew_vessel,
                                                         lockserver_handle, geniuser)
  
  for (vessel, exception_message) in parallel_results["exception"]:
      raise InternalError("Unexpected exception occurred during parallelized " + 
                          "renewal of vessels: " + exception_message)
  




@log_function_call
def _do_renew_vessel(vessel, geniuser):
  
  if vessel.acquired_by_user != geniuser:
    # The vessel was either already released, someone is trying to do things
    # they shouldn't, or we have a bug.
    log.info("Not renewing vessel " + str(vessel) + 
             " because it is not acquired by user " + str(geniuser))
    return
    
  maindb.set_maximum_vessel_expiration(vessel)

