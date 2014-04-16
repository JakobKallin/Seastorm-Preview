"""
<Program>
  transition_canonical_to_onepercentmanyevents.py

<Purpose>
  The purpose of this program is to transition nodes from the
  canonical state to the onepercentmanyevents state by bypassing
  through the movingtoonepercentmanyevents state.

<Started>
  August 13, 2009

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Usage>
  Ensure that seattlegeni and seattle are in the PYTHONPATH. 
  Ensure that the database is setup properly and django settings
    are set correctly.

  python transition_canonical_to_onepercentmanyevents.py 
"""


import os
import random
import traceback

from seattlegeni.common.api import backend
from seattlegeni.common.api import maindb
from seattlegeni.common.api import nodemanager

from seattlegeni.common.util.decorators import log_function_call

from seattlegeni.common.exceptions import *

from seattlegeni.node_state_transitions import node_transition_lib






# The full path to the onepercentmanyevents.resources file, including the filename.
RESOURCES_TEMPLATE_FILE_PATH = os.path.join(os.path.dirname(__file__), "resource_files", "onepercentmanyevents.resources")






@log_function_call
def onepercentmanyevents_divide (node_string, node_info, database_nodeobject, onepercent_resourcetemplate):
  """
  <Purpose>
    The purpose of this function is to take a node thats in canonical state
    with one vessel, and split it into the 1% vessels so the vessels can
    be acquired by users.

  <Arguments>
    node_string - the name of the node. ip:port or NAT:port

    node_info - a dictionary containing information about the node

    database_nodeobject - a database object for the node
 
    onepercent_resourcetemplate - the file that has information about resources

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

  node_transition_lib.log("Beginning onepercentmanyevents_divide on node: "+node_string)

  # Extract the ip/NAT and the port.
  # Note that the first portion of the node might be an ip or a NAT string.
  (ip_or_nat_string, port_num) = node_transition_lib.split_node_string(node_string)
  
  donated_vesselname = database_nodeobject.extra_vessel_name

  # Retrieve the usable ports list for the node and then shuffle
  # the ports so each vessel gets a random subset of the ports
  usable_ports_list = nodemanager.get_vessel_resources(ip_or_nat_string, port_num, donated_vesselname)['usableports']
  node_transition_lib.log("List of usable ports in node: "+node_string+". "+str(usable_ports_list))
  random.shuffle(usable_ports_list)

  #the vessel that we start with
  current_vessel = donated_vesselname
  node_transition_lib.log("Name of starting vessel: "+current_vessel)

  # Keep splittiing the vessel until we run out of resources.  
  # Note that when split_vessel is called the left vessel 
  # has the leftover (extra vessel)and the right vessel has 
  # the vessel with the exact resources.
  while len(usable_ports_list) >= 10:
    desired_resourcedata = get_resource_data(onepercent_resourcetemplate, usable_ports_list)
                           
    #use the first 10 ports so remove them from the list of usable_ports_list
    used_ports_list = usable_ports_list[:10]
    usable_ports_list = usable_ports_list[10:]

    node_transition_lib.log("Ports we are going to use for the new vessel: "+str(used_ports_list))
    node_transition_lib.log("Starting to split vessel: "+current_vessel)

    # Split the current vessel. The exact vessel is the right vessel 
    # and the extra vessel is the left vessel. 
    try:
      leftover_vessel, new_vessel = backend.split_vessel(database_nodeobject, current_vessel, desired_resourcedata)
    except NodemanagerCommunicationError, e:
      # The object 'e' will already include traceback info that has the actual node error.
      # If the failure is due to inability to split further, that's ok.
      if 'Insufficient quantity:' in str(e):
        node_transition_lib.log("Could not split " + current_vessel + 
                                " any further due to insufficient resource/quantity. " + str(e))
        # We must break out of the while loop here. If we let the exception get,
        # raised, it will look like the transition failed.
        break
      raise

    node_transition_lib.log("Successfully split vessel: "+current_vessel+" into vessels: "+leftover_vessel+" and "+new_vessel)
    current_vessel = leftover_vessel

    # Make sure to update the database and record the new
    # name of the extra vessel as when backend.split_vessels()
    # is called, the old vessel does not exist anymore. 
    # Instead two new vessels are created, where the first
    # vessel is the extra vessel with leftover resources
    # and the second vessel has the actual amount of resources
    maindb.set_node_extra_vessel_name(database_nodeobject, current_vessel)

    #set the user_list for the new vesel to be empty. Remember that user_list is what determines
    #the transition state, and only the extra vessel should have this set.
    backend.set_vessel_user_keylist(database_nodeobject, new_vessel, [])
    node_transition_lib.log("Changed the userkeys for the vessel "+new_vessel+" to []")

    # Add the newly created vessel to the database and then add the ports associated with
    # the vessel to the database also.    
    try:
      node_transition_lib.log("Creating a vessel record in the database for vessel "+new_vessel+" for node "+node_string)
      vessel_object = maindb.create_vessel(database_nodeobject, new_vessel)
      node_transition_lib.log("Setting the vessel ports in the database for vessel "+new_vessel+" with port list: "+str(used_ports_list))
      maindb.set_vessel_ports(vessel_object, used_ports_list)
    except:
      raise node_transition_lib.DatabaseError("Failed to create vessel entry or change vessel entry for vessel: "+
                                               new_vessel+". "+traceback.format_exc())

  # Note: there is one last thing we need to do: set the node as active. We
  # don't want to do this here just in case setting the state key on the node
  # fails. So, rather than add a post-state-key-setting-action for each state,
  # the logic has been put right in processnode() with an if statement to look
  # for the 'onepercentmanyevents_state' as the end state. We could alternately
  # just leave it for the node to be marked as active by the 1pct-to-1pct
  # transition script, but that could introduce a delay of many minutes before
  # the node/donation becomes active.
  node_transition_lib.log("Finished splitting vessels up for the node: "+node_string)


  


@log_function_call
def get_resource_data(onepercent_resourcetemplate, usable_ports_list):
  """
  <Purpose>
    Create the resource_template and return it.

  <Arguments>
    onepercent_resourcetemplate - the resource file 

    usable_ports_list - the list of ports that the node has

  <Exception>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  # Edit the resource file to add the resources in.
  resources_data = onepercent_resourcetemplate % (str(usable_ports_list[0]), str(usable_ports_list[1]), 
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





def main():
  """
  <Purpose>
    The main function that calls the process_nodes_and_change_state() function
    in the node_transition_lib passing in the process and error functions.

  <Arguments>
    None
 
  <Exceptions>
    None

  <Side Effects>
    None
  """

  #open and read the resource file that is necessary for onepercentmanyevents
  onepercentmanyevents_resource_fd = file(RESOURCES_TEMPLATE_FILE_PATH)
  onepercentmanyevents_resourcetemplate = onepercentmanyevents_resource_fd.read()
  onepercentmanyevents_resource_fd.close()
  
  """
  build up the tuple list to call process_nodes_and_change_state()
  The transition from canonical to onepercentmanyevents happens in 3 steps.
  Step1: Move the canonical nodes to the movingtoonepercent state (the reason
    this is done is because incase some transition fails, we know that they are 
    going to be in the movingtoonepercent state.
  Step2: Next run the process function and change the state from movingtoonepercent
    state to the onepercentmanyevents state.
  Step3: Find all the nodes that failed to transition from movingtoonepercent
    state to onepercentmanyevents and transition them back to the canonical state.
  """

  state_function_arg_tuplelist = [
    ("canonical", "movingto_onepercentmanyevents", node_transition_lib.noop, node_transition_lib.noop),

    ("movingto_onepercentmanyevents", "onepercentmanyevents", onepercentmanyevents_divide, 
     node_transition_lib.noop,onepercentmanyevents_resourcetemplate),

    ("movingto_onepercentmanyevents", "canonical", node_transition_lib.combine_vessels, 
     node_transition_lib.noop)]
 
  sleeptime = 10
  process_name = "canonical_to_onepercentmanyevents"
  parallel_instances = 10

  #call process_nodes_and_change_state() to start the node state transition
  node_transition_lib.process_nodes_and_change_state(state_function_arg_tuplelist, process_name, sleeptime, parallel_instances) 





if __name__ == '__main__':
  main()
