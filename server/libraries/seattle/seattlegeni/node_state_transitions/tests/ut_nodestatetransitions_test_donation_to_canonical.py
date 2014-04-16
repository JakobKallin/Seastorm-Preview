"""
<Program>
  test_donation_to_canonical.py

<Purpose>
  Test out the donation_to_canonical transition state. Basically
  tests out the node_transition_lib.py

<Authour>
  Monzur Muhammad
  monzum@cs.washington.edu

<Started>
  Aug 21, 2009
"""
#pragma out


# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.node_state_transitions import node_transition_lib


from seattlegeni.common.api import maindb

from seattlegeni.node_state_transitions.tests import mockutil

#vessel dictionary for this test
vessels_dict = {}
vessels_dict[mockutil.extra_vessel_name] = {"userkeys" : [node_transition_lib.transition_state_keys['acceptdonation']],
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

  # Create a user who has the donation key.
  maindb.create_user(mockutil.testusername, "password", "example@example.com", "affiliation", 
                    "10 11", "2 2 2", mockutil.donor_key_str)

  # Setup all the mock functions
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_lockserver_calls()
  mockutil.mock_backend_generate_key([mockutil.per_node_key_str])
  mockutil.mock_nodemanager_get_vesselresources()
  mockutil.mock_transitionlib_do_advertise_lookup([mockutil.node_address])
  mockutil.mock_backend_set_vessel_owner_key()
  mockutil.mock_backend_split_vessel()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.transition_state_keys['canonical'])])
 



def run_success_test():
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

  transitionlist = []

  transitionlist.append(("acceptdonation", "canonical", 
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info()

  assert(mockutil.set_vessel_owner_key_call_count == 1)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)  




def run_database_situation_two_test():
  """
  <Purpose>
    The purpose of this test is to test the case where a record
    for the node has been registered in the database, but the 
    owner key on the node has not been changed and no donation
    record has been created.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  # Create a database entry for the node
  node_object = maindb.create_node(mockutil.nodeid_key_str, mockutil.node_ip, mockutil.node_port, "10.0test",
                                  False, mockutil.per_node_key_str, mockutil.extra_vessel_name)  

  transitionlist = []

  transitionlist.append(("acceptdonation", "canonical", 
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))

  print "Running test where database has record of node, no record of donation and node has donor key"

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info()

  assert(mockutil.set_vessel_owner_key_call_count == 1)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)




def run_database_situation_three_test():
  """
  <Purpose>
    The purpose of this test is to test the case where a record
    for the node has been registered in the database and a 
    record for the donation has been registered, but the
    owner key on the node has not been changed.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  # Create a database entry for the node
  node_object = maindb.create_node(mockutil.nodeid_key_str, mockutil.node_ip, mockutil.node_port, "10.0test",
                                  False, mockutil.per_node_key_str, mockutil.extra_vessel_name)

  user_object = maindb.get_user(mockutil.testusername)

  # Create a donation for user
  maindb.create_donation(node_object, user_object, "Making a donation")

  transitionlist = []

  transitionlist.append(("acceptdonation", "canonical", 
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))

  print "Running test where database has record of node, has record of donation and node has donor key"

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info()

  assert(mockutil.set_vessel_owner_key_call_count == 1)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)





def run_multiple_donation_test():
  """
  <Purpose>
    The purpose of this test is to see how the transtion script would
    react if we provide a dictionary where a vessel is in the acceptdonation
    state but the node has already in the canonical state. This is possible
    if the node had two vessel in the acceptdonation state to start with.
    This is essentially if the node has two donations. Currently we don't handle
    multiple donations from the second node, so when we run the test, the success
    count should be 0 and the failure count should be 1. Also the name of the extra
    vessel should not change.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    None
  """
 
  # Have the extra vessel in canonical form
  vessels_dict[mockutil.extra_vessel_name]["userkeys"] = [node_transition_lib.transition_state_keys['canonical']]

  # Have a second vessel in acceptdonation state. Essentially a second donation.
  vessels_dict["second_donation"] = {"userkeys" : [node_transition_lib.transition_state_keys['acceptdonation']],
                                   "ownerkey" : mockutil.donor_key,
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}

  # Create a database entry for the node
  node_object = maindb.create_node(mockutil.nodeid_key_str, mockutil.node_ip, mockutil.node_port, "10.0test",
                                  False, mockutil.per_node_key_str, mockutil.extra_vessel_name)
  user_object = maindb.get_user(mockutil.testusername)
  # Create a donation for user
  maindb.create_donation(node_object, user_object, "Making a donation")
  
  # Register the new vesseldict so get_info returns this new modified vesseldict
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)




  transitionlist = []

  transitionlist.append(("acceptdonation", "canonical", 
                         node_transition_lib.noop,
                         node_transition_lib.noop, False))

  print "Running test where database has record of node, no record of donation and node has donor key"

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 0)
  assert(failure_count == 1)

  assert_database_info()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  assert(mockutil.set_vessel_user_keylist_call_count == 0)





def assert_database_info():

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





def teardown_test():

  # Cleanup the test database.
  testlib.teardown_test_db()




if __name__ == "__main__":

  setup_test()
  try:
    run_success_test()
  finally:
    teardown_test()

  setup_test()
  try:
    run_database_situation_two_test()
  finally:
    teardown_test()

  setup_test()
  try:
    run_database_situation_three_test()
  finally:
    teardown_test()

  setup_test()
  try:
    run_multiple_donation_test()
  finally:
    teardown_test()

