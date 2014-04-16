"""
<Program>
  test_canonical_to_twopercent.py

<Purpose>
  Test out the canonical_to_twopercent transition state. 
  Test for the movement from canonical to movingto_twopercent
  then test for movingto_twopercent to twopercent

<Authour>
  Monzur Muhammad
  monzum@cs.washington.edu

<Started>
  Nov 15, 2010
"""

#pragma out

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.node_state_transitions import node_transition_lib
from seattlegeni.node_state_transitions import transition_canonical_to_twopercent

from seattlegeni.common.api import maindb

from seattlegeni.node_state_transitions.tests import mockutil

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")






#vessel dictionary for this test
vessels_dict = {}
vessels_dict[mockutil.extra_vessel_name] = {"userkeys" : [node_transition_lib.transition_state_keys['canonical']],
                                   "ownerkey" : mockutil.donor_key,
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}
vessels_dict["vessel_non_seattlegeni"] = {"userkeys" : [node_transition_lib.transition_state_keys['canonical']],
                                   "ownerkey" : mockutil.donor_key,
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}
vessels_dict["random_vessel"] = {"userkeys" : ["some random key"],
                                   "ownerkey" : mockutil.donor_key,
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}








def setup_test():
  """
  <Purpose>
    Prepare everything in order to run the tests.

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
                                  False, mockutil.per_node_key_str, mockutil.extra_vessel_name)

  # Create a donation for user
  maindb.create_donation(node_object, user_object, "Making a donation")

  # Setup all the mock functions
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_lockserver_calls()
  mockutil.mock_backend_generate_key([mockutil.per_node_key_str])
  mockutil.mock_nodemanager_get_vesselresources()
  mockutil.mock_transitionlib_do_advertise_lookup([mockutil.node_address])
  mockutil.mock_backend_set_vessel_owner_key()
  mockutil.mock_backend_split_vessel()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['movingto_twopercent'])])
 



def run_can_to_movingto_twopercent_test():
  """
  <Purpose>
    Run the test and make sure that the database was modified
    properly, the right keys were set, and generally all information
    is what was expected.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  print "Starting canonical to movingto_twopercent test....."
  transitionlist = []

  transitionlist.append(("canonical", "movingto_twopercent", 
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))
  


  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_before_completed()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)  





def run_movingto_twopercent_to_twopercent_test():

  transitionlist = []


  # Change the vessel_dict and reset all the mock functions in order to have the appropriate info
  vessels_dict[mockutil.extra_vessel_name]["userkeys"] = [node_transition_lib.transition_state_keys['movingto_twopercent']]  

  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_backend_set_vessel_owner_key()
  mockutil.mock_backend_split_vessel()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['twopercent'])])

  twopercent_resource_fd = file(transition_canonical_to_twopercent.RESOURCES_TEMPLATE_FILE_PATH)
  twopercent_resourcetemplate = twopercent_resource_fd.read()
  twopercent_resource_fd.close()

  


  transitionlist.append(("movingto_twopercent", "twopercent",
                         node_transition_lib.split_vessels,
                         node_transition_lib.noop, True,
                         twopercent_resourcetemplate))

  print "Starting movingto_twopercent to twopercent test....."

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_after_completed()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  
  # Note that the call to set_vessel_user_keylist should be 10.
  # 9 time for splitting the vessels and setting keylist to []
  # and one time for setting the actual state of the node.
  assert(mockutil.set_vessel_user_keylist_call_count == 10)

  testuser = maindb.get_user(mockutil.testusername)

  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  vessel_list_per_node = maindb.get_vessels_on_node(node)

  #testing to see if the vessels exist after splitting
  assert(mockutil.split_vessel_call_count == 9)
  assert(len(vessel_list_per_node) == 9)

  for i in range(len(vessel_list_per_node)):
    # Note that the vessel names go from 1-9 rather then 0-8
    assert(vessel_list_per_node[i].node == node)
    assert(vessel_list_per_node[i].name == "new_vessel"+str(1+i))

  assert(node.extra_vessel_name == "extra_vessel_split9")




def run_movingto_twopercent_to_canonical_test():

  transitionlist = []


  # Change the vessel_dict and reset all the mock functions in order to have the appropriate info
  testuser = maindb.get_user(mockutil.testusername)

  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node

  # Create 9 vessels for this node
  for i in range(9):
    vessels_dict["vessel"+str(i)]={}
    vessels_dict["vessel"+str(i)]["userkeys"] = []
    vessels_dict["vessel"+str(i)]["ownerkey"] = rsa_string_to_publickey(node.owner_pubkey)
    vessels_dict["vessel"+str(i)]["ownerinfo"] = ""
    vessels_dict["vessel"+str(i)]["status"] = ""
    vessels_dict["vessel"+str(i)]["advertise"] = True

    maindb.create_vessel(node, "vessel"+str(i))



  vessels_dict[mockutil.extra_vessel_name]["userkeys"] = [node_transition_lib.transition_state_keys['movingto_twopercent']]
  vessels_dict[mockutil.extra_vessel_name]["ownerkey"] = rsa_string_to_publickey(node.owner_pubkey)

  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_backend_set_vessel_owner_key()
  mockutil.mock_backend_join_vessels()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['canonical'])])


  transitionlist.append(("movingto_twopercent", "canonical",
                         node_transition_lib.combine_vessels,
                         node_transition_lib.noop, False))

  print "Starting movingto_twopercent to canonical test....."

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info_before_completed()

  assert(mockutil.set_vessel_owner_key_call_count == 0)

  assert(mockutil.set_vessel_user_keylist_call_count == 1)

  all_donations = maindb.get_donations_by_user(testuser, include_inactive_and_broken=True)
  node = all_donations[0].node
  
  vessel_list_per_node = maindb.get_vessels_on_node(node)

  #testing to see if the vessels were deleted after join_vessels was called
  assert(mockutil.join_vessels_call_count == 9)
  assert(len(vessel_list_per_node) == 0)
  assert(node.extra_vessel_name == "extra_vessel_join9")





def assert_database_info_before_completed():

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





def assert_database_info_after_completed():

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
  setup_test()
  try:
    run_can_to_movingto_twopercent_test()
  finally:
    teardown_test()

  setup_test()
  try:
    run_movingto_twopercent_to_twopercent_test()
  finally:
    teardown_test()

  setup_test()
  try:
    run_movingto_twopercent_to_canonical_test()
  finally:
    teardown_test()
  
  print "All Tests Passed!"
