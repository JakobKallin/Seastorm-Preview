"""
<Program>
  ut_nodestatetransitions_test_onepercentmanyevents_to_canonical.py

<Purpose>
  Test the backend process transition_onepercentmanyevents_to_canonical.py.
  This is done in three steps. First we test the process of moving nodes
  from the onepercentmanyevents state to the movingto_canonical state,
  then we test the process of nodes moving from the movingto_canonical
  state to the canonical state. Then we test the process of nodes moving
  from the movingto_canonical state to the onepercentmanyevents state.

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Started>
  November 16, 2010
"""


#pragma out

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.node_state_transitions import node_transition_lib

from seattlegeni.node_state_transitions import transition_onepercentmanyevents_to_canonical
from seattlegeni.common.api import maindb

from seattlegeni.node_state_transitions.tests import mockutil

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")





#vessel dictionary for this test
vessels_dict_basic = {}
vessels_dict_basic[mockutil.extra_vessel_name] = {"userkeys" : [node_transition_lib.transition_state_keys['onepercentmanyevents']],
                                                  "ownerkey" : mockutil.per_node_key,
                                                  "ownerinfo" : "",
                                                  "status" : "",
                                                  "advertise" : True}
vessels_dict_basic["vessel_non_seattlegeni"] = {"userkeys" : [node_transition_lib.transition_state_keys['onepercentmanyevents']],
                                                "ownerkey" : mockutil.donor_key,
                                                "ownerinfo" : "",
                                                "status" : "",
                                                "advertise" : True}
vessels_dict_basic["random_vessel"] = {"userkeys" : ["some random key"],
                                       "ownerkey" : mockutil.donor_key,
                                       "ownerinfo" : "",
                                       "status" : "",
                                       "advertise" : True}



# The vessels dict we will populate in setup.
vessels_dict = {}


def setup_general():
  """
  <Purpose>
    Prepare all the general stuff in order to run the tests.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Efects>
    None

  <Return>
    None
  """

  testlib.setup_test_db()

  # Make sure all the variables are its default values
  mockutil.mockutil_cleanup_variables()

  # Create a user who has the donation key.
  user_object = maindb.create_user(mockutil.testusername, "password", "example@example.com", "affiliation",
                    "10 11", "2 2 2", mockutil.donor_key_str)

  # Create a database entry for the node
  node_object = maindb.create_node(mockutil.nodeid_key_str, mockutil.node_ip, mockutil.node_port, "10.0test",
                                  True, mockutil.per_node_key_str, mockutil.extra_vessel_name)


  # Create a donation for user
  maindb.create_donation(node_object, user_object, "Making a donation")

  testuser = maindb.get_user(mockutil.testusername)

  # Retrieve the info about the donation we just made.
  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  global vessels_dict
  vessels_dict = vessels_dict_basic.copy()
  # Create 9 different vessels, assuming that the original vessel got split into 9.
  for i in range(9):
    vessels_dict["vessel"+str(i)]={}
    vessels_dict["vessel"+str(i)]["userkeys"] = []
    vessels_dict["vessel"+str(i)]["ownerkey"] = rsa_string_to_publickey(node.owner_pubkey)
    vessels_dict["vessel"+str(i)]["ownerinfo"] = ""
    vessels_dict["vessel"+str(i)]["status"] = ""
    vessels_dict["vessel"+str(i)]["advertise"] = True

    maindb.create_vessel(node, "vessel"+str(i))


  # Setup all the mock functions
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_lockserver_calls()
  mockutil.mock_backend_generate_key([mockutil.per_node_key_str])
  mockutil.mock_nodemanager_get_vesselresources()
  mockutil.mock_transitionlib_do_advertise_lookup([mockutil.node_address])
  mockutil.mock_backend_set_vessel_owner_key()




def setup_onepercentmanyevents_to_moving_to_canonical():
  """
  <Purpose>
    Setup everything thats needed to run the
    onepercentmanyevents_to_movingto_canonical test.

  <Arguments>
    None.

  <Side Effects>
    None.

  <Return>
    None.
  """
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
        node_transition_lib.transition_state_keys['movingto_canonical'])])





def setup_movingto_canonical_to_onepercent():
  """
  <Purpose>
    Setup everything thats needed to run the 
    movingto_canonical_to_onepercent test.

  <Arguments>
    None.

  <Side Effects>
    None.

  <Return>
    None.
  """

  testuser = maindb.get_user(mockutil.testusername)

  # Retrieve the info about the donation we just made.
  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  # Delete all the vessel records from the database. Assume that the nodes were
  # joined back by this point.
  maindb.delete_all_vessels_of_node(node)

  # Do the setup for this test.
  vessels_dict[mockutil.extra_vessel_name]['userkeys'] = [node_transition_lib.transition_state_keys['movingto_canonical']]
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_backend_split_vessel()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['onepercentmanyevents'])])






def setup_movingto_canonical_to_canonical():
  """
  <Purpose>
    Setup everything thats needed to run the
    movingto_canonical_to_canonical test.

  <Arguments>
    None.

  <Side Effects>
    None.

  <Return>
    None.
  """

  # Do the setup for this test.
  vessels_dict[mockutil.extra_vessel_name]['userkeys'] = [node_transition_lib.transition_state_keys['movingto_canonical']]
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_backend_join_vessels()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['canonical'])])





def run_onepercentmanyevents_to_movingto_canonical():
  """
  <Purpose>
    Test the process of transitioning a node from the 
    onepercentmanyevents state to the movingto_canonical
    state.

  <Arguments>
    None

  <Side Effects>
    None

  <Exceptions>
    AssertionError raised if test fails.

  <Return>
    None
  """

  print "Starting onepercentmanyevents to movingto_canonical test....."
  transitionlist = []

  transitionlist.append(("onepercentmanyevents", "movingto_canonical",
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))



  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_non_active()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)





def run_movingto_canonical_to_canonical():
  """
  <Purpose>
    Test the process of transitioning a node from the
    movingto_canonical state to the canonical
    state.

  <Arguments>
    None

  <Side Effects>
    None

  <Exceptions>
    AssertionError raised if test fails.

  <Return>
    None
  """

  print "Starting movingto_canonical to canonical test....."
  transitionlist = []

  transitionlist.append(("movingto_canonical", "canonical",
                         node_transition_lib.combine_vessels,
                         node_transition_lib.noop, False))



  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_non_active()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)

  # Retrieve the donated node and check its status with the database.
  testuser = maindb.get_user(mockutil.testusername)
  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  vessel_list_per_node = maindb.get_vessels_on_node(node)

  #testing to see if the vessels were deleted after join_vessels was called
  assert(mockutil.join_vessels_call_count == 9)
  assert(len(vessel_list_per_node) == 0)
  assert(node.extra_vessel_name == "extra_vessel_join9")






def run_movingto_canonical_to_onepercentmanyevents():
  """
  <Purpose>
    Test the process of transitioning a node from the
    movingto_canonical state to the onepercentmanyevents
    state.

  <Arguments>
    None

  <Side Effects>
    None

  <Exceptions>
    AssertionError raised if test fails.

  <Return>
    None
  """

  print "Starting movingto_canonical to onepercentmanyevents test....."
  transitionlist = []

  onepercentmanyevents_resource_fd = file(transition_onepercentmanyevents_to_canonical.RESOURCES_TEMPLATE_FILE_PATH)
  onepercentmanyevents_resourcetemplate = onepercentmanyevents_resource_fd.read()
  onepercentmanyevents_resource_fd.close()

  transitionlist.append(("movingto_canonical", "onepercentmanyevents",
                         node_transition_lib.split_vessels,
                         node_transition_lib.noop, True, 
                         onepercentmanyevents_resourcetemplate))



  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_active()

  assert(mockutil.set_vessel_owner_key_call_count == 0)

  # The count for setting user key list is 10, once for the extra vessel
  # and 9 times for splitting the vessel.
  assert(mockutil.set_vessel_user_keylist_call_count == 10)

  # Retrieve the donated node and check its status with the database.
  testuser = maindb.get_user(mockutil.testusername)
  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  vessel_list_per_node = maindb.get_vessels_on_node(node)

  # Testing to see if the vessels were created after split_vessels was called
  assert(mockutil.split_vessel_call_count == 9)
  assert(len(vessel_list_per_node) == 9)

  for i in range(len(vessel_list_per_node)):
    # Note that the vessel names go from 1-9 rather then 0-8
    assert(vessel_list_per_node[i].node == node)
    assert(vessel_list_per_node[i].name == "new_vessel"+str(1+i))

  assert(node.extra_vessel_name == "extra_vessel_split9")





def assert_database_info_non_active():

  active_nodes_list = maindb.get_active_nodes()
  assert(len(active_nodes_list) == 0)

  testuser = maindb.get_user(mockutil.testusername)

  active_donations = maindb.get_donations_by_user(testuser)
  assert(len(active_donations) == 0)

  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  assert(len(all_donations) == 1)

  node = all_donations[0].node

  assert(node.node_identifier == mockutil.nodeid_key_str)
  assert(node.last_known_ip == mockutil.node_ip)
  assert(node.last_known_port == mockutil.node_port)
  assert(node.extra_vessel_name == mockutil.extra_vessel_name)
  assert(node.owner_pubkey == mockutil.per_node_key_str)





def assert_database_info_active():

  active_nodes_list = maindb.get_active_nodes()

  assert(len(active_nodes_list) == 1)
  assert(active_nodes_list[0].node_identifier == mockutil.nodeid_key_str)
  assert(active_nodes_list[0].last_known_ip == mockutil.node_ip)
  assert(active_nodes_list[0].last_known_port == mockutil.node_port)
  assert(active_nodes_list[0].extra_vessel_name == mockutil.extra_vessel_name)
  assert(active_nodes_list[0].owner_pubkey == mockutil.per_node_key_str)

  testuser = maindb.get_user(mockutil.testusername)
  donations_list = maindb.get_donations_by_user(testuser)

  assert(len(donations_list) == 1)
  assert(donations_list[0].node == active_nodes_list[0])





def teardown_test():

  # Cleanup the test database.
  testlib.teardown_test_db()






if __name__ == "__main__":
  setup_general()
  setup_onepercentmanyevents_to_moving_to_canonical()
  try:
    run_onepercentmanyevents_to_movingto_canonical()
  finally:
    teardown_test()

  setup_general()
  setup_movingto_canonical_to_canonical()
  try:
    run_movingto_canonical_to_canonical()
  finally:
    teardown_test()

  setup_general()
  setup_movingto_canonical_to_onepercent()
  try:
    run_movingto_canonical_to_onepercentmanyevents()
  finally:
    teardown_test()
  print "All Tests Passed!"
