"""
<Program>
  transition_donation_to_canonical.py

<Purpose>
  The purpose of this program is to transition nodes from the
  donation state to the canonical state. The canonical state
  is the state from which we can do anything sensible. It is the
  state that all nodes should return to eventually before going
  to the next state

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


import node_transition_lib





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

  state_function_arg_tuplelist = [("acceptdonation", "canonical",  node_transition_lib.noop, node_transition_lib.noop, False)]

  sleeptime = 10
  process_name = "donation_to_canonical"
  parallel_instances = 10

  #call process_nodes_and_change_state() to start the node state transition
  node_transition_lib.process_nodes_and_change_state(state_function_arg_tuplelist, process_name, sleeptime, parallel_instances)





if __name__ == '__main__':
  main()
