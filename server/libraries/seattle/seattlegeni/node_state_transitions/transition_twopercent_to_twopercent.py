"""
<Program>
  transition_twopercent_to_twopercent.py

<Purpose>
  The purpose of this program is to update the database about the 
  node, so new things such as seattle version and other stuff are
  reflected in the database

<Started>
  November 10, 2010

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Usage>
  Ensure that seattlegeni and seattle are in the PYTHONPATH.
  Ensure that the database is setup properly and django settings
    are set correctly.

  python transition_twopercent_to_twopercent.py
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

  # Mark the node as active.
  mark_node_active = True
  state_function_arg_tuplelist = [
    ("twopercent", "twopercent", node_transition_lib.update_database, 
     node_transition_lib.noop, mark_node_active, node_transition_lib.update_database_node)]

  sleeptime = 10
  process_name = "twopercent_to_twopercent"
  parallel_instances = 10

  #call process_nodes_and_change_state() to start the node state transition
  node_transition_lib.process_nodes_and_change_state(state_function_arg_tuplelist, process_name, sleeptime, parallel_instances)





if __name__ == '__main__':
  main()
