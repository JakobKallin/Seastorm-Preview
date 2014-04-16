
# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.tests import mocklib

from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import validations

from seattlegeni.website.control import interface

from seattlegeni.website.tests import testutil

import unittest



mocklib.mock_lockserver_calls()





class SeattleGeniTestCase(unittest.TestCase):


  def setUp(self):
    # Setup a fresh database for each test.
    testlib.setup_test_db()



  def tearDown(self):
    # Cleanup the test database.
    testlib.teardown_test_db()



  def test_regenerate_user_key(self):
    
    pubkey = "1 2"
    privkey = "3 4 5"
    donor_key = "6 7"
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", 
                              pubkey, privkey, donor_key)
    userport = user.usable_vessel_port

    vesselcount = 4
    
    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * vesselcount
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])

    # Acquire all vessels on behalf of this user.
    all_vessels_list = interface.acquire_vessels(user, vesselcount, 'rand')

    # Release 2 vessels.
    released_vessels_list = all_vessels_list[:2]
    kept_vessels_list = all_vessels_list[2:]
    interface.release_vessels(user, released_vessels_list)
    
    # Ensure all of the vessels are marked as having user keys in sync.
    for vessel in all_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertTrue(vessel.user_keys_in_sync)

    # We expect a single key to be generated through the keygen api (the new
    # user public key).
    mocklib.mock_keygen_generate_keypair([("55 66", "77 88 99")])
    
    interface.change_user_keys(user, pubkey=None)
    
    # Get a new user object from the database.
    user = maindb.get_user(user.username)
    
    # Make sure the user's key changed.
    self.assertEqual(user.user_pubkey, "55 66")
    self.assertEqual(user.user_privkey, "77 88 99")
    
    # Make sure that all of the vessels the user has access to (and no other
    # vessels) are marked as needing user keys to be sync'd.
    # Ensure all of the vessels are marked as having user keys in sync.
    for vessel in kept_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertFalse(vessel.user_keys_in_sync)

    for vessel in released_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertTrue(vessel.user_keys_in_sync)





  def test_set_user_key(self):
    
    pubkey = "1 2"
    privkey = "3 4 5"
    donor_key = "6 7"
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", 
                              pubkey, privkey, donor_key)
    userport = user.usable_vessel_port

    vesselcount = 4
    
    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * vesselcount
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])

    # Acquire all vessels on behalf of this user.
    all_vessels_list = interface.acquire_vessels(user, vesselcount, 'rand')

    # Release 2 vessels.
    released_vessels_list = all_vessels_list[:2]
    kept_vessels_list = all_vessels_list[2:]
    interface.release_vessels(user, released_vessels_list)
    
    # Ensure all of the vessels are marked as having user keys in sync.
    for vessel in all_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertTrue(vessel.user_keys_in_sync)

    # We expect no keys to be generated through the keygen api.
    mocklib.mock_keygen_generate_keypair([])
    
    interface.change_user_keys(user, pubkey="55 66")
    
    # Get a new user object from the database.
    user = maindb.get_user(user.username)
    
    # Make sure the user's key changed.
    self.assertEqual(user.user_pubkey, "55 66")
    self.assertEqual(user.user_privkey, None)
    
    # Make sure that all of the vessels the user has access to (and no other
    # vessels) are marked as needing user keys to be sync'd.
    # Ensure all of the vessels are marked as having user keys in sync.
    for vessel in kept_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertFalse(vessel.user_keys_in_sync)

    for vessel in released_vessels_list:
      # Get a fresh vessel from the db.
      vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
      self.assertTrue(vessel.user_keys_in_sync)





  def test_set_invalid_user_key(self):
    
    pubkey = "1 2"
    privkey = "3 4 5"
    donor_key = "6 7"
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", 
                              pubkey, privkey, donor_key)
    
    func = interface.change_user_keys
    args = (user, "abc")
    self.assertRaises(ValidationError, func, *args)





def run_test():
  unittest.main()



if __name__ == "__main__":
  run_test()
