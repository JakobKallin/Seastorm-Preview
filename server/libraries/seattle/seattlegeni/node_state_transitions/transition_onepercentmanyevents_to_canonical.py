"""
<Program>
  transition_onepercentmanyevents_to_canonical.py

<Purpose>
  Recently we have modified our resources file and going 
  to allocate a different amount of resources for each
  of the vessels. In order to do that we are going to have
  to transition the old nodes that are in the onepercentmanyevents
  state to a new state that we are going to call twopercent state.
  This is due to the fact the new vessels will have 2% cpu power
  instead of the 1% power it used to have. It will pass through
  the canonical state to get to the twopercent state. We already
  have a transition script that goes from the canonical state
  to the twopercent state, so we just have to bring all the 
  current nodes that are in the onepercent state to the canonical
  state.

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Usage>
  Ensure that seattlegeni and seattle are in the PYTHONPATH.
  Ensure that the database is setup properly and django settings
    are set correctly.

  python transition_onepercentmanyevents_to_canonical.py
"""

import os

from seattlegeni.common.exceptions import *

from seattlegeni.common.util.decorators import log_function_call

import node_transition_lib



# The full path to the onepercentmanyevents.resources file, including the filename.
RESOURCES_TEMPLATE_FILE_PATH = os.path.join(os.path.dirname(__file__), "resource_files", "onepercentmanyevents.resources")


def main():
  """
  <Purpose>
    This is the main launching point for this script. We are going
    to call the node_transition_lib and start the process of 
    moving from onepercentmanyevents state to the canonical state
    through an intermediate state the moving_to_canonical state.
    This wasy if anything fails, we can go back to the onepercent 
    state.

  <Arguments>
    None.

  <Exceptions>
    None

  <Side Effects>
    A lot of nodes are altered.

  <Return>
    None.
  """


  # Open and read the resource file that is necessary for onepercentmanyevents
  onepercentmanyevents_resource_fd = file(RESOURCES_TEMPLATE_FILE_PATH)
  onepercentmanyevents_resourcetemplate = onepercentmanyevents_resource_fd.read()
  onepercentmanyevents_resource_fd.close()


  # Create a  list that is used to call node_transition_lib.
  # The list will have a list of three tuples. The first 
  # tuple will transition all the onepercentmanyevents state
  # to the moving_to_canonical state. This will use noop functions.
  # We will not actually perform any actions. Next we will transition
  # all the moving_to_canonical state nodes to the canonical state by
  # performing a join operation on all the vessels, to combine all the
  # vessels on one node into one giant node that it was before it got 
  # split. 
  # In the next phase we will transition all the moving_to_canonical
  # state nodes into the onepercentmanyevents state. This is for the 
  # case where we might have failed to combine the vessels and move
  # to canonical state, so we want to restore them back to the 
  # onepercent state.

  
  # We are not going to mark any of the nodes active in the database, 
  # as we are joining the vessels back together.
  mark_nodes_inactive=False

  state_function_arg_tuplelist = [
    ("onepercentmanyevents", "movingto_canonical", 
     node_transition_lib.noop, node_transition_lib.noop, mark_nodes_inactive),

    ("movingto_canonical", "canonical", 
     node_transition_lib.combine_vessels, node_transition_lib.noop, mark_nodes_inactive),

    ("movingto_canonical", "onepercentmanyevents_state", 
     node_transition_lib.split_vessels, node_transition_lib.noop, mark_nodes_inactive, 
     onepercentmanyevents_resourcetemplate)]


  # Some constant variables we will use to call node_transition_lib.
  sleeptime = 10
  process_name = "onepercentmanyevents_to_canonical"
  parallel_instances = 10

  # Call the process_node_and_change_state() function to attempt to 
  # transition all the nodes from onepercentmanyevents to canonical.
  node_transition_lib.process_nodes_and_change_state(state_function_arg_tuplelist, 
                                                     process_name, sleeptime, 
                                                     parallel_instances)






if __name__ == '__main__':
  main()
