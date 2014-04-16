"""
<Program>
  nodestatus.py

<Started>
  16 August 2009

<Author>
  Justin Samuel

<Purpose>
  This module provides a function, check_node(), which can be used to compare
  the information we have about a node in the database with the actual data
  the node reports. Optionally, the check_node() function will mark nodes as
  broken and release/mark for cleanup any vessels that are in an invalid
  state.
  
  Note that this module may be useful on the admin side of the website just
  for allowing an administrator to see what's wrong with a node. It's
  worth noting that this module isn't thread-safe, so if two requests made
  by administrators ran at the same time, the reported results they get back
  might be incorrect (especially if they are querying the same node at the same
  time). This lack of thread safety won't cause inaccurate actions to be taken
  on the database, though, because locks are used when not in readonly mode.
  
  A simple and lazy solution if lack of thread-safety becomes annoying would
  be to put the global data that is collected in a threading.local() data store
  and so not have to change much of the code. You might think that you could
  just require locks to be held for readonly requests, but that only reduces
  the problem, it doesn't eliminate it.

  TODO: check vessel ports
"""

import os

from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb
from seattlegeni.common.api import nodemanager

from seattlegeni.common.util import log as log_module

from seattlegeni.common.exceptions import *

from seattlegeni.website import settings

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")


# Restore the log module as repy's log function is copied into our
# namespace when we are importing rsa.repy
log = log_module




def _readfilecontents(filename):
  f = open(filename)
  contents = f.read()
  f.close()
  return contents





# Decrease the amount of logging output.
log.loglevel = log.LOG_LEVEL_INFO

# A dictionary where the names are names we use to refer to the keys and the
# values are the names of the public key files. All public key files will be
# considered relative to the directory specified in 
# settings.SEATTLECLEARINGHOUSE_STATE_KEYS_DIR.
statekeyfiles = {"acceptdonation" : "acceptdonation.publickey",
                 "canonical" : "canonical.publickey",
                 "onepercentmanyevents" : "onepercentmanyevents.publickey",
                 "movingto_onepercentmanyevents" : "movingto_onepercentmanyevents.publickey",
                 "twopercent" : "twopercent.publickey",
                 "movingto_twopercent" : "movingto_twopercent.publickey",
                 "movingto_canonical" : "movingto_canonical.publickey"
                 }

statekeys = {}
for keyname in statekeyfiles:
  keyfilefullpath = os.path.join(settings.SEATTLECLEARINGHOUSE_STATE_KEYS_DIR, statekeyfiles[keyname])
  statekeys[keyname] = rsa_string_to_publickey(_readfilecontents(keyfilefullpath))





# We'll keep track which nodes had problems.
nodes_with_problems = {}

# This holds a list of nodes/vessels where action either was taken or would
# have been taken if checknode was called with readonly set to False.
actionstaken = {"recorded_communication_failure":[],
                "node_marked_inactive":[],
                "node_marked_broken":[],
                "vessel_released":[]}





def _report_node_problem(node, message):
  global nodes_with_problems
  
  if not node.node_identifier in nodes_with_problems:
    nodes_with_problems[node.node_identifier] = []
  
  nodes_with_problems[node.node_identifier].append(message)
  
  log.info("Problem on node " + str(node) + ": " + message)





def get_node_problem_info():
  """
  <Purpose>
    Get the information about node problems collected from previous calls to
    check_node().
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A dictionary whose keys are the node identifiers and the values are lists
    of strings that describe the problems encountered.
  """
  return nodes_with_problems





def get_actions_taken():
  """
  <Purpose>
    Get the information about what database actions were taken for nodes and
    vessels.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A dictionary whose keys are the the names of actions taken and the values
    are lists of nodes or vessels the actions were taken on.
  """
  return actionstaken





def reset_collected_data():
  """
  <Purpose>
    Reset the node problem info and actions taken that is collected.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    All previously collected node problem info has been discarded. The list of
    actions taken is also reset.
  <Returns>
    None
  """
  global nodes_with_problems
  nodes_with_problems = {}
  
  for action in actionstaken:
    actionstaken[action] = []





def _record_node_communication_failure(readonly, node):
  if node not in actionstaken["recorded_communication_failure"]:
    actionstaken["recorded_communication_failure"].append(node)
    
  if readonly:
    log.info(str(node) + " Not recording communication failure because called in readonly mode.")
  else:
    log.info(str(node) + " Recording communication failure.")
    maindb.record_node_communication_failure(node)





def _mark_node_inactive(readonly, node):
  if node not in actionstaken["node_marked_inactive"]:
    actionstaken["node_marked_inactive"].append(node)
    
  if readonly:
    log.info(str(node) + " Not marking node as inactive because called in readonly mode.")
  else:
    log.info(str(node) + " Marking node as inactive.")
    maindb.mark_node_as_inactive(node)





def _mark_node_broken(readonly, node):
  if node not in actionstaken["node_marked_broken"]:
    actionstaken["node_marked_broken"].append(node)
  
  if node.is_broken:
    log.info(str(node) + " Not marking node as broken because it is already broken.")
  else:
    if readonly:
      log.info(str(node) + " Not marking node as broken because called in readonly mode.")
    else:
      log.info(str(node) + " Marking node as broken.")
      maindb.mark_node_as_broken(node)





def _release_vessel(readonly, vessel):
  if vessel not in actionstaken["vessel_released"]:
    actionstaken["vessel_released"].append(vessel)
  
  if readonly:
    log.info(str(vessel) + " Not recording vessel as released because called in readonly mode.")
  else:
    log.info(str(vessel) + " Recording vessel as released.")
    maindb.record_released_vessel(vessel)




    
def check_node(node, readonly=True, lockserver_handle=None):
  """
  <Purpose>
    Check a node for problems. This will try to contact the node and will
    compare the information retrieved from the node to the information we
    have in our database. It will log and collect the information about
    the problems. The problem information can be retrieved program
  <Arguments>
    node
      The Node object of the node to be checked.
    readonly
      False if the function should mark the node in the database as inactive
      or broken (and vessels released) when appropriate, True if it should
      never change anything in the database. Default is True.
    lockserver_handle
      If an existing lockserver handle should be used for lock acquisitions,
      it should be provided here. Otherwise, a new lockserver handle will
      be used the during of this function call.
      Note: no locking is done if readonly is True. That is, if there is
      no reason to lock a node, there is no reason to provide a
      lockserver_handle.
  <Exceptions>
    None
  <Side Effects>
    If readonly is False, the database may be updated appropriately based on
    what the function sees. No changes are ever directly made to the nodes
    through nodemanager communication regardless of the setting of readonly.
    However, other scripts might take action based on database changes (e.g.
    released vessel will quickly be cleaned up by the backend daemon).
  <Returns>
    None
  """
    
  if not readonly:
    must_destroy_lockserver_handle = False
    
    if lockserver_handle is None:
      must_destroy_lockserver_handle = True
      lockserver_handle = lockserver.create_lockserver_handle()
      
    if not readonly:
      lockserver.lock_node(lockserver_handle, node.node_identifier)
    
  # Be sure to release the node lock, if we are locking the node.
  try:
    # Get a fresh node record from the database. It might have changed before
    # we obtained the lock.
    node = maindb.get_node(node.node_identifier)
    
    # The code beyond this point would be a good candidate for splitting out
    # into a few smaller functions for readability.
    
    donation_list = maindb.get_donations_from_node(node)
    if len(donation_list) == 0:
      _report_node_problem(node, "The node has no corresponding donation records. " +
                           "Not marking node broken, though.")
    
    try:
      nodeinfo = nodemanager.get_node_info(node.last_known_ip, node.last_known_port)
    except NodemanagerCommunicationError:
      _record_node_communication_failure(readonly, node)
      _report_node_problem(node, "Can't communicate with node.")
      return
    
    try:
      nodekey_str = rsa_publickey_to_string(nodeinfo["nodekey"])
    except ValueError:
      _mark_node_broken(readonly, node)
      _report_node_problem(node, "Invalid nodekey: " + str(nodeinfo["nodekey"]))
      return
    
    # Check that the nodeid matches. If it doesn't, it probably means seattle
    # was reinstalled or there is a different system at that address now.
    if node.node_identifier != nodekey_str:
      _mark_node_inactive(readonly, node)
      _report_node_problem(node, "Wrong node identifier, the node reports: " + str(nodeinfo["nodekey"]))
      # Not much more worth checking in this case.
      return
    
    
    # Check that the database thinks it knows the extra vessel name.
    if node.extra_vessel_name == "":
      _mark_node_broken(readonly, node)
      _report_node_problem(node, "No extra_vessel_name in the database.")
      # Not much more worth checking in this case.
      return
    
    # Check that a vessel by the name of extra_vessel_name exists on the node.
    if node.extra_vessel_name not in nodeinfo["vessels"]:
      _mark_node_broken(readonly, node)
      _report_node_problem(node, "The extra_vessel_name in the database is a vessel name that doesn't exist on the node.")
      # Not much more worth checking in this case.
      return
    
    extravesselinfo = nodeinfo["vessels"][node.extra_vessel_name]
        
    vessels_in_db = maindb.get_vessels_on_node(node)
  
    if len(extravesselinfo["userkeys"]) != 1:
      _mark_node_broken(readonly, node)
      _report_node_problem(node, "The extra vessel '" + node.extra_vessel_name + 
                          "' doesn't have 1 user key, it has " + 
                          str(len(extravesselinfo["userkeys"])))
  
    else:    
      # Figure out which state the node is in according to the state key.
      recognized_state_name = ""
    
      for statename in statekeys:
        if statekeys[statename] == extravesselinfo["userkeys"][0]:
          recognized_state_name = statename
    
      if not recognized_state_name:
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "The extra vessel '" + node.extra_vessel_name + 
                            "' doesn't have a recognized user/state key")
    
      if len(vessels_in_db) == 0:
        if recognized_state_name == "onepercentmanyevents" or recognized_state_name == "twopercent":
          # We don't mark it as broken because it may be in transition by a
          # transition script away from onepercentmanyevents. If the vessels
          # in the db have been deleted first but the state key hasn't been
          # changed yet, we might hit this. Also, it's not so bad to have it
          # not be marked as broken when it's like this, as it has no vessels
          # we know about, anyways, so we're not going to be giving questionable
          # resources to users because of it.
          _report_node_problem(node, "The node is in the " + recognized_state_name + " state " + 
                              "but we don't have any vessels for it in the database.")
      else:
        if recognized_state_name != "onepercentmanyevents" and recognized_state_name != "twopercent":
          # We don't mark it as broken because it may be in transition by a
          # transition script. Also, we may have other states in the future
          # besides onepercentmanyevents that have vessels. We don't want
          # to make all of those nodes inactive if it's just an issue of
          # someone forgot to update this script.
          _report_node_problem(node, "The node is in the '" + recognized_state_name + 
                              "' state but we have vessels for it in the database.")
      
    known_vessel_names = []
    for vessel in vessels_in_db:
      known_vessel_names.append(vessel.name)
  
    # Look for vessels on the node with our node ownerkey which aren't in our database.
    for actualvesselname in nodeinfo["vessels"]:
  
      vessel_ownerkey = nodeinfo["vessels"][actualvesselname]["ownerkey"]
      
      try:
        vessel_ownerkey_str = rsa_publickey_to_string(vessel_ownerkey)
      except ValueError:
        # At this point we aren't sure it's our node, but let's assume that if
        # there's an invalid key then the node is broken, period.
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "Invalid vessel ownerkey: " + str(vessel_ownerkey))
        return
      
      if vessel_ownerkey_str == node.owner_pubkey:
        if actualvesselname not in known_vessel_names and actualvesselname != node.extra_vessel_name:
          _mark_node_broken(readonly, node)
          _report_node_problem(node, "The vessel '" + actualvesselname + "' exists on the node " + 
                              "with the ownerkey for the node, but it's not in our vessels table.")
  
    # Do some checking on each vessel we have in our database.
    for vessel in vessels_in_db:
      
      # Check that the vessel in our database actually exists on the node.
      if vessel.name not in nodeinfo["vessels"]:
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "The vessel '" + vessel.name + "' in our db doesn't exist on the node.")
        continue
  
      vesselinfo = nodeinfo["vessels"][vessel.name]
  
      try:
        vessel_ownerkey_str = rsa_publickey_to_string(vesselinfo["ownerkey"])
      except ValueError:
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "Invalid vessel ownerkey on a vessel in our db: " + str(vessel_ownerkey))
        return
  
      # Check that the owner key for the vessel is what we have for the node's owner key in our database.
      if node.owner_pubkey != vessel_ownerkey_str:
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "The vessel '" + vessel.name + "' doesn't have the ownerkey we use for the node.")
      
      if not vesselinfo["advertise"]:
        _mark_node_broken(readonly, node)
        _report_node_problem(node, "The vessel '" + vessel.name + "' isn't advertising.")
      
      # We're only concerned with non-dirty vessels as the backend daemon
      # should be working on cleaning up dirty vessels.
      if not vessel.is_dirty:
        # Check that the user keys that have access are the ones that should have access.
        users_with_access = maindb.get_users_with_access_to_vessel(vessel)
        
        if len(users_with_access) != len(vesselinfo["userkeys"]):
          _release_vessel(readonly, vessel)
          _report_node_problem(node, "The vessel '" + vessel.name + "' reports " + 
                              str(len(vesselinfo["userkeys"])) + " user keys, but we expected " + str(len(users_with_access)))
          
        for user in users_with_access:
          if rsa_string_to_publickey(user.user_pubkey) not in vesselinfo["userkeys"]:
            _release_vessel(readonly, vessel)
            _report_node_problem(node, "The vessel '" + vessel.name + "' doesn't have the userkey for user " + user.username + ".")

  finally:
    # We didn't do any locking if this readonly was True.
    if not readonly:
      
      # Release the lock
      lockserver.unlock_node(lockserver_handle, node.node_identifier)
      
      # Destroy the lockserver handle if we created it ourselves.
      if must_destroy_lockserver_handle:
        lockserver.destroy_lockserver_handle(lockserver_handle)

