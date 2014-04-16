"""
Tests the interface.renew_vessels and interface.renew_all_vessels calls.
"""
#pragma out
#pragma error OK

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.tests import mocklib

from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

from seattlegeni.website.control import interface

from seattlegeni.website.tests import testutil

import datetime
import unittest





mocklib.mock_lockserver_calls()





class SeattleGeniTestCase(unittest.TestCase):


  def setUp(self):
    # Setup a fresh database for each test.
    testlib.setup_test_db()



  def tearDown(self):
    # Cleanup the test database.
    testlib.teardown_test_db()



  def test_renew_vessels_insufficient_vessel_credits(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = 4
    
    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * vesselcount
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])
    
    # Acquire all of the vessels the user can acquire.
    vessel_list = interface.acquire_vessels(user, vesselcount, 'rand')
    
    # Decrease the user's vessel credits to one less than the number of vessels
    # they have acquired.
    user.free_vessel_credits = 0
    user.save()
    
    func = interface.renew_vessels
    args = (user, vessel_list)
    self.assertRaises(InsufficientUserResourcesError, func, *args)      
  
    func = interface.renew_all_vessels
    args = (user,)
    self.assertRaises(InsufficientUserResourcesError, func, *args)   



  def test_renew_some_of_users_vessel(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = 4
    
    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * vesselcount
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])
    
    # Acquire all of the vessels the user can acquire.
    vessel_list = interface.acquire_vessels(user, vesselcount, 'rand')
    
    renew_vessels_list = vessel_list[:2]
    not_renewed_vessels_list = vessel_list[2:]
    
    interface.renew_vessels(user, renew_vessels_list)
  
    now = datetime.datetime.now()
    timedelta_oneday = datetime.timedelta(days=1)
  
    for vessel in renew_vessels_list:
      self.assertTrue(vessel.date_expires - now > timedelta_oneday)

    for vessel in not_renewed_vessels_list:
      self.assertTrue(vessel.date_expires - now < timedelta_oneday)



  def test_renew_vessels_dont_belong_to_user(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    # Create a second user.
    user2 = maindb.create_user("user2", "password", "user2@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    vesselcount = 4
    
    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * vesselcount
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])
    
    # Acquire all of the vessels the user can acquire.
    vessel_list = interface.acquire_vessels(user, vesselcount, 'rand')
    
    release_vessel = vessel_list[0]
    interface.release_vessels(user, [release_vessel])
    
    # Manually fiddle with one of the vessels to make it owned by user2.
    user2_vessel = vessel_list[1]
    user2_vessel.acquired_by_user = user2
    user2_vessel.save()
    
    # Try to renew all of the originally acquired vessels, including the ones
    # that were released. We expect these to just be ignored.
    interface.renew_vessels(user, vessel_list)
  
    # Get fresh vessel objects that reflect the renewal.
    remaining_vessels = interface.get_acquired_vessels(user)
    release_vessel = maindb.get_vessel(release_vessel.node.node_identifier, release_vessel.name)
    user2_vessel = maindb.get_vessel(user2_vessel.node.node_identifier, user2_vessel.name)
   
    now = datetime.datetime.now()
    timedelta_oneday = datetime.timedelta(days=1)
  
    # Ensure that the vessels the user still has were renewed but that the ones
    # the user released were ignored (not renewed).
    for vessel in remaining_vessels:
      self.assertTrue(vessel.date_expires - now > timedelta_oneday)

    self.assertTrue(user2_vessel.date_expires - now < timedelta_oneday)
    
    self.assertEqual(release_vessel.date_expires, None)
  




def run_test():
  unittest.main()



if __name__ == "__main__":
  run_test()
