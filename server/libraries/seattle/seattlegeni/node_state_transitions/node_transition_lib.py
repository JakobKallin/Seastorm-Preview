"""
<Program>
  node_transition_lib.py

<Started>
  July 29, 2009

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Purpose>
  This is a library file for the node transition scripts. It is a general 
  module so all the transition scripts will be able to import this file 
  and easily create a new transition script.

<Usage>
  Meant to be imported.

<Information>
  The transitional script is meant to seek out all the nodes that 
  are currently advertising and check their states. If necessary, 
  the state of the node is changed. Currently a node can be in three 
  different state: donated state, canonical state, and one percent state. 
  The donated state is when new nodes are discovered. This is usually 
  when a new user installs seattle and donates resources. The transitional
  scripts finds all the nodes that have been donated and processes them. 
  The information about the donated nodes are added to the database and 
  the node state is changed to the canonical state. The canonical state 
  is an important state, as this is the state where the nodes are ready to 
  be used, and be split up. All nodes should be able to come back to the 
  canonical state if anything goes wrong. At this point the canonical state 
  is changed to the onepercent state. This is where the 10% resource is
  taken and split into 10 sections (or into 1% resources). This 1% resource 
  is the vessel. Thus a node manager is responsible for 10 vessels (by 
  default, if only 10% resource is donated). In the future we might have 
  other states such as a twopercent state, in case we want to split the 
  resource differently.
"""

import os
import sys
import time
import random
import traceback

import django.db

from seattle import runonce
from repyportability import *

import seattlegeni.common.util.log

from seattlegeni.common.api import maindb
from seattlegeni.common.api import backend
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import nodemanager

# For setting the backend authcode.
import seattlegeni.backend.config

from seattlegeni.common.util.decorators import log_function_call

from seattlegeni.common.exceptions import *

from seattlegeni.website import settings

# Import all the repy files.
add_dy_support(locals())
dy_import_module_symbols('advertise.repy')
dy_import_module_symbols('rsa.repy')
dy_import_module_symbols('listops.repy')
dy_import_module_symbols('parallelize.repy')
dy_import_module_symbols('random.repy')





# Whether _init_node_transition_lib() has been called yet.
is_initialized = False





def _retrieve_state_key(key_file_name):
  """ Retrieve pubkey from file and return the dictionary form of key"""
  return rsa_file_to_publickey(os.path.join(settings.SEATTLECLEARINGHOUSE_STATE_KEYS_DIR, key_file_name))  


known_transition_states = ['canonical', 'acceptdonation', 
                           'movingto_onepercentmanyevents', 
                           'movingto_canonical', 'twopercent',
                           'onepercentmanyevents',
                           'movingto_twopercent']

transition_state_keys = {}

for state in known_transition_states:
  transition_state_keys[state] = _retrieve_state_key(state + '.publickey')




@log_function_call
def process_nodes_and_change_state(change_nodestate_function_tuplelist, transition_script_name, sleeptime, parallel_instances=1):
  """
  <Purpose>
    locate all the nodes in a certain state and apply the function thats in 
    the change_state_function_tuplelist and change the node state. Uses 
    public key to identify the nodes in different states.

  <Arguments>
    change_state_function_tuplelist - a list of tuples that contains all
      the info to change the state of a node.
      Tuple arguments:
        ((startstate_name, startstate_publickey), (endstate_name, endstate_publickey), 
         processfunction, errorfunction, processfunc_args)

    transition_script_name - a unique name used to get a process lock.

    sleeptime - the amount of time to sleep between node processing.

    parallelinstances - the number of threads to run in parallel.

  <Exceptions>
    None
  <Side Effects>
    None

  <Return>
    None
  """
  
  _init_node_transition_lib()
  
  log("Starting state transition script: "+transition_script_name+".....")

  # Get a processlock so multiple versions of the same script aren't running.
  if runonce.getprocesslock("process_lock."+transition_script_name) != True:
    log("The lock for "+transition_script_name+" is being held.\nExiting...\n\n")
    return

  # Continuously run the script and keep checking for nodes whose state needs to be changed.
  while True:
    do_one_processnode_run(change_nodestate_function_tuplelist, transition_script_name, parallel_instances)
    log("Finished running do_one_processnode_run(), going to sleep for "+str(sleeptime)+" seconds")  
    time.sleep(sleeptime)
    log("Waking up from sleep.....")





@log_function_call
def do_one_processnode_run(change_nodestate_function_tuplelist, transition_script_name, parallel_instances=1):
  """
  <Purpose>
    This is the actual script that runs and starts everything up. It gets the list 
    of nodes that needs to be changed. Then starts up the function that tranistions
    the nodes in parallel.

  <Arguments> 
    change_state_function_tuplelist - a list of tuples that contains all
      the info to change the state of a node.
      Tuple arguments:
        (startstate_name, endstate_name, processfunction, 
         errorfunction, mark_node_active, processfunc_args)

    transition_script_name - a unique name used to get a process lock.

    sleeptime - the amount of time to sleep in seconds between node processing.

    parallelinstances - the number of threads to run in parallel.

  <Exceptions>
    None
  <Side Effects>
    None

  <Return>
    [(success_processrun_count, fail_processrun_count)]

      success_processrun_count - how many nodes were processed sucessfully
      fail_processrun_count - how many nodes were processed unsuccessfully
  """
  
  result_list = []
  # Going through the list of node state functions.
  for change_nodestate_function_tuple in change_nodestate_function_tuplelist:
    # Get some of the information out of the nodestate_function tuple.
    startstate_name = change_nodestate_function_tuple[0]
    endstate_name = change_nodestate_function_tuple[1]

    startstate_publickey = transition_state_keys[startstate_name]



    # Lookup nodes with the startstate publickey, on failure log info and continue.
    log("Looking up nodes to transition from "+startstate_name+" state to "+endstate_name+" state")
    successful_lookup, nodeprocesslist = find_advertised_nodes(startstate_name, startstate_publickey)



    # If lookup was unsuccessful, then continue on. info is logged in find_advertised_nodes().
    if not successful_lookup:
      log("find_advertised_nodes() failed to look up nodes. Going on to the next nodestate_function_tuple")
      continue



    else:
      log("List of ip/NAT found in advertise_lookup(): " + str(nodeprocesslist))
      log("Length of nodeprocesslist: " + str(len(nodeprocesslist))) 
      log("Starting run_parallel_process to spawn threads to process nodes...")

    # Call the function that runs the processnode function on all the nodes in parallel.
    success_processrun_count, fail_processrun_count = run_parallel_processes(nodeprocesslist, 
                                                                             transition_script_name, 
                                                                             parallel_instances, 
                                                                             *change_nodestate_function_tuple)

   
    # Return the number of failures and successes.
    log("Succeeded on "+str(success_processrun_count)+" nodes, Failed on "+str(fail_processrun_count)+" nodes")
    result_list.append( (success_processrun_count, fail_processrun_count) )

    
    # Since we do a lot of lookup in the database we are going to have
    # a lot of database objects since django caches all the lookups.
    # We have to clear these queries so our memory usage doesn't grow
    # over time.
    django.db.reset_queries()

  return result_list   




@log_function_call
def run_parallel_processes(nodeprocesslist, lockname, parallel_instances, *processargs):
  """
  <Purpose>
    Create parallel handle and run the node process functions in parallel.

  <Arguments>
    nodeprocesslist - the list of all the nodes that needs to be processed

    lockname - the name of the lock that was acquired earlier. To ensure
      that the lock is still held    

    *processargs - this includes startstate, endstate, 
      nodeprocess_func, nodeerror_func and nodeprocess_args 

  <Exceptions>
    No exceptions are raised but on excepts, everything is logged.

  <Side Effects>
    None

  <Return>
    (success_count, failure_count)

      success_count - The number of nodes that we successfully changed state
      failure_count - The number of nodes that we failed to change state
  """

  try:
    # Note that processnode is a function.
    parallel_handle = parallelize_initfunction(nodeprocesslist, processnode, parallel_instances, *processargs)

  except: 
    log("Error: failed to set up parallelize_initfunction" + traceback.format_exc())
    return (0, len(nodeprocesslist)) 




  try:
    # Keep looping until all the threads in the parallel handle are finished running.
    while not parallelize_isfunctionfinished(parallel_handle):
      # Check to see if the process lock is still being held.
      if not runonce.stillhaveprocesslock("process_lock."+lockname):
        log("The lock for "+lockname+" has been lost. Exiting transitional script")
        sys.exit(1)
    
      # Sleep for a second to give the parallel_handle enought time to finish.
      time.sleep(1)

    # Get the results to the parallel_handle for the node processing.
    nodeprocessresults = parallelize_getresults(parallel_handle)


    success_count = 0
    failure_count = 0

    # Account for all the successful results.
    for nodename, returnvalue in nodeprocessresults['returned']:
      if returnvalue:
        log("Success on node "+nodename+". Returnvalue: "+str(returnvalue))
        success_count += 1
      else:
        log("Failure on node "+nodename+".")
        failure_count += 1


    # Write to the log for all the nodes that had an exception.
    for nodename, exceptionstring in nodeprocessresults['exception']:
      log("Failure on node "+nodename+"\nException String: "+exceptionstring+"\n")
      failure_count += 1

  
    # Write to the log for all the nodes that were aborted.
    for nodename in nodeprocessresults['aborted']:
      log("The processnode_function was aborted for the node "+nodename)
      failure_count += 1


  finally:
    # Clean up the parallel_handle and make sure that the handle is closed.
    log("Cleaning up and closing parallel_handle")
    parallelize_closefunction(parallel_handle)

  # Everything worked out fine in the parallel_handle.
  return (success_count, failure_count)




    
@log_function_call
def processnode(node_string, startstate_name, endstate_name, nodeprocess_func, nodeerror_func, mark_node_active, *nodeprocess_args):
  """
  <Purpose>
    First check the current state of the node, to ensure that it is in the
    correct state. Then run the nodeprocess_func on the node to process
    the node. Then set the new state of the node once the node has been
    processed properly.

  <Arguments>
    node_string - this is the node itself that is gotten from advertise_lookup,
      most likely an ip:port address or NAT:ip.

    startstate_name - the state in which the nodes are in now.

    endstate_name - the state we want to transition the nodes to.

    nodeprocess_func - the function that is used to process the node

    nodeerror_func - the function that is run, if there is an error

    mark_node_active - This bit determines if we want to mark the node
      as an active node or not.

    nodeprocess_args - the arguments for nodeprocess_func

  <Exceptions>
    NodeError - raised if the node is in a weird state, or if the 
      node does not exist

    NodemanagerCommunicationError - raised if problem communicating the node

    DatabaseError - raised if unable to access database

    UnexpectedError - if some unusual error occurs thats not caught by others

  <Side Effects>
    Database may get modified

  <Return>
    Return true if processing the node was successful, otherwise return false
    if any exceptions occured
  """
 
  # The pubkey for the state.
  startstate_pubkey = transition_state_keys[startstate_name]
  endstate_pubkey = transition_state_keys[endstate_name]

  # Make sure that the node is just not an empty string. 
  # The node_string could be bad due to bad advertise_lookup.
  if not node_string:
    raise NodeError("An empty node was passed down to processnode() with startstate: "+
                   startstate_name)

  # Note that the first portion of the node might be an ip or a NAT string.
  (ip_or_nat_string, port_num) = split_node_string(node_string)

  log("Starting to process node: "+node_string)

  # Try to retrieve the vessel dictionary for a node, 
  # on error raise a NodeError exception.
  try:
    node_info = nodemanager.get_node_info(ip_or_nat_string, port_num)
  except NodemanagerCommunicationError:
    raise
    

  # Extract the nodeID in order to acquire a lock
  nodeID =  _do_rsa_publickey_to_string(node_info['nodekey'])
  
  # Acquire a node lock
  lockserver_handle = acquire_node_lock(nodeID)

  try:
    log("Retrieving node vesseldict for node: "+node_string)   
    node_info = nodemanager.get_node_info(ip_or_nat_string, port_num)
   
    log("Successfully retrieved node_info for node: " + node_string)

    # If the nodes are in acceptdonationstate, update/check the database
    # to ensure that it matches the node information.
    if startstate_pubkey == transition_state_keys['acceptdonation']:
      add_new_node_to_db(node_string, node_info)         
      log("Successfully added node to the database for node" + node_string)
      log("The database should reflect the node information accurately")

    # Get the database object    
    database_nodeobject = maindb.get_node(nodeID)

    # Retrieve the node state and and the list of vessels.
    current_node_state_pubkey = get_node_state(node_info, database_nodeobject)
 
    # Make sure that the node is in the right state.
    if current_node_state_pubkey != startstate_pubkey:
      log("The node is not in the right transition state. NodeID is: " + nodeID +
          " Current state is " + str(current_node_state_pubkey) +
          ". Should be in state " + str(startstate_pubkey))
      raise NodeError("Node is no longer in the right state!")
  
    # Run the processnode function that was passed originally from the transition scripts.
    try:
      nodeprocess_func(node_string, node_info, database_nodeobject, *nodeprocess_args)
    except:
      log("Failed to process node: " + node_string)
      raise NodeError("Could not process node: " + node_string + traceback.format_exc())

    # Set the node state now that the node has been processed.
    if startstate_pubkey != endstate_pubkey:
      log("Trying to set new state for node: " + node_string)
      set_node_state(database_nodeobject, endstate_pubkey)
      
      # If the mark_node_active bit was set, then we want to mark the node
      # as active in the database. Until the node is marked active, the user
      # may not get credited. This is usually set at the final stage when all
      # vessels have been split.
      if mark_node_active:
        maindb.mark_node_as_active(database_nodeobject)
      else:
        maindb.mark_node_as_inactive(database_nodeobject)
        
      log("Finished setting new state " + endstate_name + " on node " + node_string) 

    else:
      log("Not setting node state: start state and end state are the same.")

  except NodeError:
    log("Node data problem when processing node: " + node_string + traceback.format_exc())
    return False    
  except NodemanagerCommunicationError:
    log("Node communication failed while processing node: " + node_string)
    return False
  except DatabaseError:
    log("Ran into problem accessing database while processing node: " + node_string)
    return False
  except UnexpectedError:
    log("Ran into some unexpected error while processing node: " + node_string)
    return False
  finally:
    release_node_lock(lockserver_handle, nodeID)

  #everything worked out fine
  return True  





@log_function_call
def get_node_state(node_info, database_nodeobject):
  """
  <Purpose>
    Given a node, find out what state the node is in (canonical, onepercent,
    acceptdonation). And return the state of the node. The node state should
    be held in the extra vessel, which should have only one userkey

  <Arguments>
    node_info - a dictionary that contains information about the node

    database_nodeobject - a node object that was retrieved from the
      database for the current node.

  <Exceptions>
    NodeError - raised if the extra vessel is not found in the node_info or
      if the extra_vessel has multiple state keys under 'userkeys'

  <Side Effects>
    None

  <Return>
    node_state - the state that the node is in.
  """

  log("Starting get node state for node " + database_nodeobject.node_identifier)
  extra_vessel_name = database_nodeobject.extra_vessel_name
  log("Name of extra vessel: " + extra_vessel_name)
 
  #check to see that the extra vessel exists in node_info
  if extra_vessel_name not in node_info["vessels"]:
    raise NodeError("The extra_vessel_name '" + extra_vessel_name + 
                    "' doesn't exist on the node. "+traceback.format_exc())

  extra_vessel_info = node_info["vessels"][extra_vessel_name]
  log("Extra vessel info: " + str(extra_vessel_info))

  #make sure that the extra vessel has only one state key
  if len(extra_vessel_info["userkeys"]) != 1:
    raise NodeError("The extra_vessel_name '" + extra_vessel_name +
                    "' doesn't contain one key, it contains " + 
                    str(len(extra_vessel_info["userkeys"])))
 
  return extra_vessel_info["userkeys"][0]

  

  
 
@log_function_call
def set_node_state (database_nodeobject, end_state):
  """
  <Purpose>
    given a list of vessels, change the userkeys of all the vessels.
    Only one of the vessel should carry the end_state, all other vessels
    will have empty state as transitional state. Keep in mind that the 
    userkey_list contains the transitional state of the node.
  
  <Arguments>
    end_state - the state that the node should end in.

    database_nodeobject - an object that has been retrieved from the database

  <Exceptions>
    NodeError - raised if unable to change node state
    
    NodemanagerCommunicationError - incase we are unable to retrieve node_info

  <Side Effects>
    None

  <Return>
    None
  """

  # Convert the end_state pubkey to string format and then set the key.
  final_state_str = _do_rsa_publickey_to_string(end_state)

  # Try to change the node state by setting the new state in the
  # userkeys list of the extra vessel
  try:
    backend.set_vessel_user_keylist(database_nodeobject, database_nodeobject.extra_vessel_name, [final_state_str])
  except:
    raise NodeError("Unable to change state of node: " + database_nodeobject.node_identifier + 
                    " "+traceback.format_exc())
  log("Successfully changed the node state to "+str(end_state))
  
    



@log_function_call
def add_new_node_to_db(node_string, node_info):
  """
  <Purpose> 
    when new nodes come online, they may be not have the right data in 
    the database. This function ensures that the database has the 
    appropriate data and the node_info data matches with the 
    database data. There are four different situations and we want
    to be in the fourth situation by the end of this function (if
    we don't run into any error along the way.)
    Situation1:
      Database has no entry for node or and does not have a 
      donation record. The node has the donor key as the 
      owner key.
    Situation2:
      Database has entry for the node but does not have any 
      donation record. The node has the donor key as the 
      owner key.
    Situation3:
      Database has entry for the node and it has a
      donation record. The node has the donor key as the 
      owner key.
    Situation 4:
      Database has entry for the node and it has a
      donation record. The node has the per-node key
      as the owner key.

  <Arguments>
    node_string - The node address in ip:port or NAT:port format

    node_info - A dictionary that contains information about the node

  <Exceptions>
    NodeError - if the node does not have a valid state

    DatabaseError - if there is any problem while creating node in database
      or creating record of donation in database or problem retrieving user
      object from the database

  <Side Effects>
    Database might get modified

  <Return>
    None
  """

  log("Node in acceptdonationpublickey. Calling add_newnode_to_db()" +
      " to check that node is correctly in database")
  
  log("Looking for donor key for node: " + node_string)
  log("Looking for the vessel that has the transition state in its 'userkeys'")

  nodeID = _do_rsa_publickey_to_string(node_info['nodekey'])

  (donated_vesselname, donor_key) = find_extra_vessel_name_and_donor_key(node_info, node_string)
    
  try:
    # Retrieve the node object if it's already in the database.
    # This is for the case if a database entry was created,
    # but the script ran into an error later on, causing the
    # state of the node to be not updated.
    database_nodeobject = maindb.get_node(nodeID)
  except DoesNotExistError:
    # If the node object does not exist in the database, add it.
    # This is situation 1, where nothing has been done yet.
    log("Database entry does not exist for node: " + node_string)
    database_nodeobject = create_new_node_object(node_string, node_info, donated_vesselname)
    log("Successfully added node to the database: " + node_string)    
     
  # We are finished adding node object, or retrieving node object from database.
  log("Retrieved node object successfully with nodeID: " + nodeID + 
      " with the node: " + str(database_nodeobject))
    

  # Check to see if the vessels owner key has been changed from the donor key
  # to the per node key. This is either situation 2 or situation 3.
  if donor_key != rsa_string_to_publickey(database_nodeobject.owner_pubkey):
    # Note that this is the case for if there is multiple vessels in 
    # the same node that are in the acceptdonation state. On the first 
    # run a database record was created for one vessel and a donation 
    # record was created. If we are looking at a second vessel that is
    # in the acceptdonation state, we want to raise an error and back out.
    # To do this we compare the vessel name of our original donated vessel
    # with the correct vesel name. If the names the same then everything is
    # fine as we are just recovering the vessel. If the vesselname is not
    # the same then this is a new vessel and we don't want to do anything.
    # Currently we only accept one donation from one node. In the future
    # this might change.
    if donated_vesselname != database_nodeobject.extra_vessel_name:
      raise NodeError("There is already a record of a vessel donated from node: " + node_string)
    
    log("Database has nodeID but node has donor key")
    log("Checking to make sure that the donation was credited")

    # Check to see if the donor was credited.
    donation_list = maindb.get_donations_from_node(database_nodeobject)

    # If the donation lenght is 0 then the user has not been credited
    # yet for their donation. This could be either due to this being
    # a new node that was just added or it could be because we are
    # recovering from a crash. This is in situation 2 if the length
    # of donation_list is 0
    if len(donation_list) == 0:
      log("The donation has not been credited yet for node " + node_string)
      create_donation_record(database_nodeobject, donor_key)
    else:
      log("The donation has already been credited for node " + node_string)

    log("Attempting to change the owner for vessel: " + donated_vesselname)
    
    # Convert the donation key to string format, and set the vessel owner key.
    # We should be now in situation 3 where the node exists in the database
    # and there is a donation record in the database.
    donation_owner_pubkey_str = _do_rsa_publickey_to_string(donor_key)
    backend.set_vessel_owner_key(database_nodeobject, donated_vesselname, 
                                 donation_owner_pubkey_str, 
                                 database_nodeobject.owner_pubkey)

    log("Successfully changed the owner_key to " + donation_owner_pubkey_str)

  return database_nodeobject
  # At this point we should be in situation 4 where everything is set 
  # properly. That is an entry for the node should exist in the database,
  # an entry for the donation should exist in the database and the 
  # per-node key should be the owner key for the node.





@log_function_call
def create_new_node_object(node_string, node_info, donated_vesselname):
  """
  <Purpose>
    Create a new node entry in the database with a newly generated
    per node key
  
  <Arguments>
    node_string - the address of the node 

    node_info - information about the node

    vesselname - the name of the extra vessel

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    Returns a database node object
  """ 

  nodeID = _do_rsa_publickey_to_string(node_info['nodekey'])
  (ip_or_nat_string, port_num) = split_node_string(node_string)

  # Generate a new set of keys for the node. The pubkey gets passed
  # down to us while the private key is stored in a database elsewhere.
  log("Generating new keys for node owner_key....")   
  new_node_owner_pubkey = backend.generate_key(ip_or_nat_string+". "+nodeID)
  log("Generated publickey for node "+node_string+" : "+str(new_node_owner_pubkey))
  
  try:
    # Attempt to add new node to db.
    database_nodeobject = maindb.create_node(nodeID, ip_or_nat_string, port_num, 
                                                 node_info['version'], False, 
                                                 new_node_owner_pubkey, 
                                                 donated_vesselname) 
     
    log("Added node to the database with nodeID: " + nodeID)  
  except:
    raise DatabaseError("Failed to create node and add to database. " + traceback.format_exc())    
 
  return database_nodeobject




@log_function_call
def create_donation_record(database_nodeobject, donor_key):
  """
  <Purpose>
    To create a donation record for a user in the database

  <Arguments>
    database_nodeobject - a nodeobject that was retrieved from
      the database

  <Exceptions>
    DatabaseError - raised if problem accessing the database

  <Side Effects>
    Database will get modified

  <Return>
    None
  """

  # Retrieve the user object in order to give them credit
  # for their donation using the donor key
  try:
    database_userobject = maindb.get_donor(rsa_publickey_to_string(donor_key))
    log("Retrieved the userobject of the donor from database: " +
        str(database_userobject))
  except:
    raise DatabaseError("Failed to retrieve the userobject from the database. " + 
                        traceback.format_exc())

  donation_description = "Crediting user " + str(database_userobject)+ " for donation of node " + str(database_nodeobject)
      
  # Attempt to give the user credit for their donation
  try:
    log("Attempting to credit donation for the node " + database_nodeobject.node_identifier)
    maindb.create_donation(database_nodeobject, database_userobject, 
                           donation_description)
  except:
    raise DatabaseError("Failed to credit user for donation for user: " +
                        str(database_userobject) + traceback.format_exc())

  log("Registered the donation for the user with the donor_key: " + 
      str(donor_key))





@log_function_call
def find_extra_vessel_name_and_donor_key(node_info, node_string):
  """
  <Purpose>
    A function that is used to determine the name of the extra
    vessel and the the donor key that is associated with it.

  <Arguments>
    node_info - the information about the node

  <Exceptions>
    NodeError - raised if no vessel was found

  <Side Effects>
    None
 
  <Return>
    (donation_vesselname, donation_key) 
  """
  
  # Find the extra vessel of the node. Loop through all the vessels
  # until we find a vessel which has the acceptdonationpublickey in
  # its userkey's list. 
  for vesselname in node_info['vessels']:
    log("looking in vessel "+vesselname+".....")
    if transition_state_keys['acceptdonation'] in node_info['vessels'][vesselname]['userkeys']:
      donation_key = node_info['vessels'][vesselname]['ownerkey']
      donation_vesselname = vesselname
      log("Found donation key in vessel "+donation_vesselname+" : "+
         str(donation_key))
      return (donation_vesselname, donation_key)       

  raise NodeError("Node "+node_string+" has no vessel with the acceptdonation " + 
                  "state key in the userkeys.")





@log_function_call 
def find_advertised_nodes(startstate_name, startstate_publickey):
  """
  <Purpose>
    Looks up nodes with publickeys that matches startstate_publickey. 
    If advertise_lookup fails, it sleeps and tries again. Tries upto
    10 times before it returns.

  <Arguments>
    startstate_name - the name of the state. In order for logging
    startstate_publickey - the key with which the node is identified

  <Exception>
    Nothing is raised but on failure we log the failure

  <Side Effects>
    None

  <Return>
    success, nodelist
      success - boolean, states weather advertise lookup worked
      nodelist -list of nodes that was found. Empty if advertise lookup failed

  """
 
  log("Looking for nodes with public key: \n"+str(startstate_publickey))

  #lookup nodes with the startstate_publickey. Lookup upto 10MB of nodes
  #if advertise_lookup fails, try it 10 times before moving on
  advertise_lookup_fail_count = 0
  while True:
    try:
      nodeprocesslist = _do_advertise_lookup(startstate_publickey)
      return True, nodeprocesslist

    except:
      #increment fail count
      advertise_lookup_fail_count += 1
      log("advertise_lookup failed "+str(advertise_lookup_fail_count)+
          " times, while looking up nodes in "+startstate_name+ 
          " state with pub key:\n"+str(startstate_publickey))

      #if the lookup fails 10 times, break out of the while loop and log the info
      if advertise_lookup_fail_count >= 10:
        log("advertise_lookup failed 10 times...moving on to the next state transition function")
        return False, []

      log("Sleeping for 10 second before retrying advertise_lookup...")
      time.sleep(1)






@log_function_call
def split_vessels (node_string, node_info, database_nodeobject, resourcetemplate):
  """
  <Purpose>
    The purpose of this function is to take a node has an extra vessel that is
    big enough to be split into two or more vessels. The resources on a vessel
    is determined by the resourcetemplate that is provided as well as the usable
    ports on the node.

  <Arguments>
    node_string - the name of the node. ip:port or NAT:port

    node_info - a dictionary containing information about the node

    database_nodeobject - a database object for the node

    resourcetemplate - the file that has information about resources

  <Exceptions>
    NodeError - Error raised if node is not in the right state

    NodemanagerCommunicationError - raised if we cannot retrieve the usable ports for a node

    NodeProcessError - raised if unable to split vessels properly

    DatabaseError - raised if unable to modify the database

  <Side Effects>
    Database gets modified.

  <Return>
    None
  """

  log("Beginning to divide vessel on node: "+node_string)

  # Extract the ip/NAT and the port.
  # Note that the first portion of the node might be an ip or a NAT string.
  (ip_or_nat_string, port_num) = split_node_string(node_string)

  donated_vesselname = database_nodeobject.extra_vessel_name

  # Retrieve the usable ports list for the node and then shuffle
  # the ports so each vessel gets a random subset of the ports
  usable_ports_list = nodemanager.get_vessel_resources(ip_or_nat_string, port_num, donated_vesselname)['usableports']
  log("List of usable ports in node: "+node_string+". "+str(usable_ports_list))
  random.shuffle(usable_ports_list)

  #the vessel that we start with
  current_vessel = donated_vesselname
  log("Name of starting vessel: "+current_vessel)

  # Keep splittiing the vessel until we run out of resources.
  # Note that when split_vessel is called the left vessel
  # has the leftover (extra vessel)and the right vessel has
  # the vessel with the exact resources.
  while len(usable_ports_list) >= 10:
    desired_resourcedata = get_resource_data(resourcetemplate, usable_ports_list)

    #use the first 10 ports so remove them from the list of usable_ports_list
    used_ports_list = usable_ports_list[:10]
    usable_ports_list = usable_ports_list[10:]

    log("Ports we are going to use for the new vessel: "+str(used_ports_list))
    log("Starting to split vessel: "+current_vessel)

    # Split the current vessel. The exact vessel is the right vessel
    # and the extra vessel is the left vessel.
    try:
      leftover_vessel, new_vessel = backend.split_vessel(database_nodeobject, current_vessel, desired_resourcedata)
    except NodemanagerCommunicationError, e:
      # The object 'e' will already include traceback info that has the actual node error.
      # If the failure is due to inability to split further, that's ok.
      if 'Insufficient quantity:' in str(e):
        log("Could not split " + current_vessel + " any further due to insufficient resource/quantity. " + str(e))
        # We must break out of the while loop here. If we let the exception get,
        # raised, it will look like the transition failed.
        break
      raise

    log("Successfully split vessel: "+current_vessel+" into vessels: "+leftover_vessel+" and "+new_vessel)
    current_vessel = leftover_vessel

    # Make sure to update the database and record the new
    # name of the extra vessel as when backend.split_vessels()
    # is called, the old vessel does not exist anymore.
    # Instead two new vessels are created, where the first
    # vessel is the extra vessel with leftover resources
    # and the second vessel has the actual amount of resources
    maindb.set_node_extra_vessel_name(database_nodeobject, current_vessel)

    # Set the user_list for the new vesel to be empty. Remember that user_list is what determines
    # the transition state, and only the extra vessel should have this set.
    backend.set_vessel_user_keylist(database_nodeobject, new_vessel, [])
    log("Changed the userkeys for the vessel "+new_vessel+" to []")

    # Add the newly created vessel to the database and then add the ports associated with
    # the vessel to the database also.
    log("Creating a vessel record in the database for vessel "+new_vessel+" for node "+node_string)
    try:
      vessel_object = maindb.create_vessel(database_nodeobject, new_vessel)
      log("Setting the vessel ports in the database for vessel "+new_vessel+" with port list: "+str(used_ports_list))
      maindb.set_vessel_ports(vessel_object, used_ports_list)
    except:
      raise DatabaseError("Failed to create vessel entry or change vessel entry for vessel: " +
                          new_vessel + ". " + traceback.format_exc())


  log("Finished splitting vessels up for the node: "+node_string)





@log_function_call
def get_resource_data(resourcetemplate, usable_ports_list):
  """
  <Purpose>
    Create the resource_template and return it.

  <Arguments>
    resourcetemplate - the resource file

    usable_ports_list - the list of ports that the node has

  <Exception>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  # Edit the resource file to add the resources in.
  resources_data = resourcetemplate % (str(usable_ports_list[0]), str(usable_ports_list[1]),
                                       str(usable_ports_list[2]), str(usable_ports_list[3]),
                                       str(usable_ports_list[4]), str(usable_ports_list[5]),
                                       str(usable_ports_list[6]), str(usable_ports_list[7]),
                                       str(usable_ports_list[8]), str(usable_ports_list[9]),
                                       str(usable_ports_list[0]), str(usable_ports_list[1]),
                                       str(usable_ports_list[2]), str(usable_ports_list[3]),
                                       str(usable_ports_list[4]), str(usable_ports_list[5]),
                                       str(usable_ports_list[6]), str(usable_ports_list[7]),
                                       str(usable_ports_list[8]), str(usable_ports_list[9]))

  return resources_data





@log_function_call
def combine_vessels(node_string, node_info, database_nodeobject):
  """
  <Purpose>
    The purpose of this function is to combine all the vessels of 
    a node into the extra vessel.

  <Arguments>
    node_string - the name of the node. ip:port or NAT:port

    node_info - the information about the node including the vesseldict

    database_nodeobject - This is the nodeobject that was retrieved from our database

    node_state_pubkey - This is the state that the node should be in. After all the 
      vessels are combined, the final vessel should have this as its state

  <Exceptions>
    NodeError - raised if unable to combine the vessels together

    DatabaseError - raised if unable to delete vessel records from database

  <Side Effects>
    None

  <Return>
    None
  """

  log("Beginning combine_vessels for the node: "+node_string)

  node_pubkey_string = database_nodeobject.owner_pubkey
    
  #This is the extra vessel or the vessel that has the transition state
  extra_vessel = database_nodeobject.extra_vessel_name 

  #the list that will hold all the vesselnames of the node
  vessel_list = get_vessel_list(node_info, node_pubkey_string, extra_vessel, node_string)

  # Combine all the vessels into one vessel.
  log("Trying to combine all the vessels...")
  create_combined_vessel(database_nodeobject, extra_vessel, vessel_list)

  try:
    # Delete all the vessel recoreds from database. 
    maindb.delete_all_vessels_of_node(database_nodeobject)
    log("Removed all the vessel records from the database for node: "+node_string)
  except:
    raise DatabaseError("Unable to delete all vessel records from the database for node "+
                        node_string+". " + traceback.format_exc())





@log_function_call
def create_combined_vessel(database_nodeobject, extra_vessel, vessel_list):
  """
  <Purpose>
    Combine all the vessels into one vessel, given a list of vessels

  <Arguments>
    database_nodeobject - a node object from the database

    extra_vessel - the name of the extra vessel

    vessel_list - a list of all the vessels that need to be
      combined with the extra vessel.

  <Exceptions>
    NodeError - raised if unable to combine vessels.

  <Side Effects>
    The individual vessels will not exist after this function is called

  <Return>
    A vessel name that is the result after all the vessels are 
    combined.
  """
  
  # Loop through all the vessels in the vessel list and do a 
  # join_vessels call to the backend to join each vessel with
  # the extra vessel. Be the end we should have only one vessel,
  # which should be the extra_vessel. Make sure to also update
  # the database with each iteration to ensure that the
  # extra_vessel_name gets updated appropriately.
  for current_vessel in vessel_list:
    try: 
      combined_vessel = backend.join_vessels(database_nodeobject, extra_vessel, current_vessel)
    except:
      raise NodeError("Unable to combine vessel " + current_vessel +
                      " with vessel " + extra_vessel + traceback.format_exc())
    
    # Update the database and change the name of the extra_vessel_name for the node
    maindb.set_node_extra_vessel_name(database_nodeobject, combined_vessel)

    log("Combined vessel " + extra_vessel + " and " + current_vessel + " into " + combined_vessel)
    log("Set database nodeobjects extra_vessel_name to " + database_nodeobject.extra_vessel_name)
    extra_vessel = combined_vessel

  log("Finished combining all the vessels for node: " + database_nodeobject.node_identifier)
  
  return extra_vessel





@log_function_call
def update_database(node_string, node_info, database_nodeobject, update_database_node):
  """
  <Purpose>
    The purpose of this function is to update the database

  <Arguments>
    node_string - the name of the node. ip:port or NAT:port

    node_info - a dictionary containing information about the node

    node_database - a node object from the database

    update_database_node - This is a function that updates the database. May be replaced
      in the future.

  <Exceptions>
    DatabaseError - raised if unable to modify the database

  <Side Effects>
    None

  <Return>
    None
  """

  log("Beginning update_database on node: "+node_string)

  # Extract the ip/NAT and the port.
  # Note that the first portion of the node might be an ip or a NAT string.
  ip_or_nat_string, port_num = split_node_string(node_string)

  # Update the database with the most up to date info about the node.
  # Currently only updates the node version
  log("Retrieved database node object for node: " + node_string)
  try:
    update_database_node(database_nodeobject, node_info, ip_or_nat_string, port_num)
  except:
    raise node_transition_lib.DatabaseError("Unable to update the database." + traceback.format_exc())

  log("updated node database record with version: "+str(database_nodeobject.last_known_version))

  return





@log_function_call
def update_database_node(database_nodeobject, node_info, ip_or_nat_string, port_num):
  """
  <Purpose>
    Update the database with the information provided

  <Arguments>
    database_nodeobject - a database object of the node

    node_info - information about the node including the vesseldict

    ip_or_nat_string - the ip or nat address of the node

    port_num - the port number that is being used for the port

    node_status - the status of the node that should be set

  <Exception>
    DatabaseError - raise if we could not update database

  <Side Effects>
    None

  <Return>
    database_object
  """

  version = node_info['version']

  # If the node objec was inactive, then we are going to make it active.
  if not database_nodeobject.is_active:
    log("The node "+ip_or_nat_string+":"+str(port_num)+" was inactive. Now activating")

  try:
    # Update all the database info about the node.
    maindb.record_node_communication_success(database_nodeobject, version, ip_or_nat_string, port_num)
  except:
    raise DatabaseError("Unable to modify database to update info on node: "+ip_or_nat_string)

  log("Updated the database for node: "+ip_or_nat_string+", with the latest info")

  return database_nodeobject





@log_function_call
def get_vessel_list(node_info, node_pubkey_string, extra_vessel, node_string):
  """
  <Purpose>
    Retrieve a list of vessels that are in this node that
    can be acquired. That is all the vessels except the 
    extra vessel.

  <Arguments>
    node_info - a dictionary with node information
    
    node_pubkey_string - this is the per-node key. Its the key
      that determines if we are the owner of the vessel.

    extra_vessel - the name of the extra vessel

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    a list of all the vessel names in this node
  """

  vessel_list = []

  node_pubkey_dict = rsa_string_to_publickey(node_pubkey_string)

  # Go through all the vessels and check if we are the owner of the
  # vessel. If we are then we add the vessel to the vessel_list,
  # which are the list of vessels that needs to be combined. 
  log("Finding all the vessels in the node "+node_string+"...")
  for current_vessel in node_info['vessels']:
    # Check to see if the vessels belong to us (SeattleGENI).
    if node_info['vessels'][current_vessel]['ownerkey'] == node_pubkey_dict:
      # Add the vessel to the list.
      vessel_list.append(current_vessel)
      log("Added vessel "+current_vessel+" to vessel_list")
      
  # Remove the starting vessel from the vessel list.
  vessel_list.remove(extra_vessel)

  return vessel_list





def split_node_string(node_string):
  """
  Convert a node string which is the address of the node
  in the form of ip:port or NAT:port, into the ip and its
  port number and return the string version of the ip/NAT
  and the int form of the port number
  """

  ip_or_nat_string, port_string = node_string.split(":")
  port_num = int(port_string)
  return (ip_or_nat_string, port_num)





#helper function now for testing.
@log_function_call
def _do_advertise_lookup(startstate_publickey):
  """ Do an advertise lookup. This function is used mainly for easier
      testing purposes. """
  nodelist = advertise_lookup(startstate_publickey, maxvals = 10*1024*1024)
  # There can sometimes be empty strings in the list returned by advertise_lookup.
  while "" in nodelist:
    nodelist.remove("")
  return nodelist





def acquire_node_lock(nodeID):
  """ 
  Create a lockserver handle and acquire a lock
  and return the lockserver handle
  """
  # Initialize a lock.
  lockserver_handle = lockserver.create_lockserver_handle()
  log("Created lockserver_handle for use on node: "+nodeID)
  # Acquire a lock for the node.
  lockserver.lock_node(lockserver_handle, nodeID)
  log("Acquired node lock for nodeID: "+nodeID)
 
  return lockserver_handle





def release_node_lock(lockserver_handle, nodeID):
  """ Release the node lock and Destroy the lockserver handle"""
  #release the node lock and destroy lock handle
  lockserver.unlock_node(lockserver_handle, nodeID)
  log("released lock for node: "+nodeID)
  lockserver.destroy_lockserver_handle(lockserver_handle)
  log("Destroyed lockserver_handle for node: "+nodeID)
  




def noop(*args):
  """ in some cases I don't want to do anything (i.e. just change state)"""
  pass



def log(message):
  """
  <Purpose>
    log information with a time stamp
  
  <Arguments>
    message - the message to log

  <Exceptions>
    None

  <Side Effects>
    log file may get edited if sterr and stdout is redirected

  <Return>
    None
  """

  seattlegeni.common.util.log.info(message)
  





def _init_node_transition_lib():
  """
  <Purpose>
    Perform one-time initialization actions on startup. This will be taken
    care of automatically, scripts don't need to worry about calling this.
  <Arguments>
    None
  <Exceptions>
    TimeUpdateError
      If time update fails in init_nodemanager().
  <Side Effects>
    All necessary initalization is done.
  <Returns>
    None
  """

  global is_initialized
  
  if not is_initialized:
    
    is_initialized = True
    
    # Set the log level if we want to override the defaults.
    #seattlegeni.common.util.log.set_log_level(seattlegeni.common.util.log.LOG_LEVEL_DEBUG)

    # We don't need to maindb.init_maindb() because that happens automatically
    # when django creates a new database connection.
    
    nodemanager.init_nodemanager()

    backend.set_backend_authcode(seattlegeni.backend.config.authcode)
    




def _do_rsa_publickey_to_string(pubkey):
  """A helper function to retrieve string form of pubkey, used for testing."""
  return rsa_publickey_to_string(pubkey)



class UnexpectedError(Exception):
  """Exception if something unexpected goes wrong."""



class NodeProcessError(Exception):
  """This exception means the node is in an invalid state."""



class NodeError(Exception):
  """This exception means the node is in an invalid state."""



class DatabaseError(Exception):
  """This exception means that the database maindb had some kind of error or did not return properly"""
