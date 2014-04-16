"""
Note that backend.release_vessel() calls that automatically happen when not 
enough of the requested vessels are acquired don't currently need to be
mock'd out because currently that function does nothing.
"""

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.tests import mocklib

from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

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



  def test_acquire_vessels_invalid_request(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    func = interface.acquire_vessels
    
    # Negative vesselcount.
    args = (user, -1, 'wan')
    self.assertRaises(AssertionError, func, *args)   

    # Zero vesselcount.
    args = (user, 0, 'wan')
    self.assertRaises(AssertionError, func, *args)   

    # Unrecognized vessel type.
    args = (user, 1, 'x')
    self.assertRaises(ProgrammerError, func, *args)   



  def test_acquire_vessels_insufficient_vessel_credits(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    # TODO: need to test maindb.require_user_can_acquire_resources separately
    
    # The user doesn't have any donations, they shouldn't be able to acquire
    # more vessels than their free credits.
    credit_limit = maindb.get_user_free_vessel_credits(user)
    
    vesseltypelist = ['wan', 'lan', 'nat', 'rand']

    for vesseltype in vesseltypelist:
      func = interface.acquire_vessels
      args = (user, credit_limit + 1, vesseltype)
      self.assertRaises(InsufficientUserResourcesError, func, *args)      
  


  def test_acquire_wan_vessels_multiple_calls_wan(self):

    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * 10
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = maindb.get_user_free_vessel_credits(user)
    
    testutil.create_nodes_on_different_subnets(vesselcount, [userport])
    
    # First request a single vessel.
    first_vessel_list = interface.acquire_vessels(user, 1, 'wan')
    
    # Now acquire all of the rest that the user can acquire.
    second_vessel_list = interface.acquire_vessels(user, vesselcount - 1, 'wan')

    self.assertEqual(1, len(first_vessel_list))
    self.assertEqual(vesselcount - 1, len(second_vessel_list))



  def test_acquire_wan_vessels_multiple_calls_lan(self):

    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * 10
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = maindb.get_user_free_vessel_credits(user)
    
    testutil.create_nodes_on_same_subnet(vesselcount, [userport])
    
    # First request a single vessel.
    first_vessel_list = interface.acquire_vessels(user, 1, 'lan')
    
    # Now acquire all of the rest that the user can acquire.
    second_vessel_list = interface.acquire_vessels(user, vesselcount - 1, 'lan')

    self.assertEqual(1, len(first_vessel_list))
    self.assertEqual(vesselcount - 1, len(second_vessel_list))



  def test_acquire_wan_vessels_multiple_calls_nat(self):

    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * 10
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = maindb.get_user_free_vessel_credits(user)
    
    testutil.create_nat_nodes(vesselcount, [userport])
    
    # First request a single vessel.
    first_vessel_list = interface.acquire_vessels(user, 1, 'nat')
    
    # Now acquire all of the rest that the user can acquire.
    second_vessel_list = interface.acquire_vessels(user, vesselcount - 1, 'nat')

    self.assertEqual(1, len(first_vessel_list))
    self.assertEqual(vesselcount - 1, len(second_vessel_list))



  def test_acquire_wan_vessels_multiple_calls_rand(self):

    # Have every vessel acquisition to the backend request succeed.
    calls_results = [True] * 10
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = maindb.get_user_free_vessel_credits(user)
    
    # Create vesselcount nodes split between the different types.
    testutil.create_nodes_on_different_subnets(4, [userport])
    testutil.create_nodes_on_same_subnet(4, [userport])
    testutil.create_nat_nodes(vesselcount - 8, [userport])
    
    # First request a single vessel.
    first_vessel_list = interface.acquire_vessels(user, 1, 'rand')
    
    # Now acquire all of the rest that the user can acquire.
    second_vessel_list = interface.acquire_vessels(user, vesselcount - 1, 'rand')

    self.assertEqual(1, len(first_vessel_list))
    self.assertEqual(vesselcount - 1, len(second_vessel_list))



  def test_acquire_wan_vessels_some_vessels_fail(self):

    # Have every other vessel acquisition fail. We're going to acquire 50,
    # so we'll need 100 responses alternating between failure and success
    # (we're starting with failure, so 100, not 99).
    calls_results = [False, True] * 50
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    # We need to give the user some donations so they have enough credits.
    # We're assuming it's 10 credits per donation.
    self.assertEqual(10, maindb.VESSEL_CREDITS_FOR_DONATIONS_MULTIPLIER)
    
    # Also make sure the user started with 10 credits.
    self.assertEqual(10, maindb.get_user_free_vessel_credits(user))
    
    # We need 100 nodes the user can acquire vessels on as we're having half of
    # the node acquisitions fail.
    testutil.create_nodes_on_different_subnets(100, [userport])
    
    # Now credit the user for donations on 4 of these.
    for node in maindb.get_active_nodes()[:4]:
      maindb.create_donation(node, user, '')
    
    # Ok, the user now has 50 vessels the can acquire and there are 100 nodes
    # with vessels available for them. Let's try to acquire all 50 at once and
    # make sure this works even though we'll have to get through 100 requests
    # to the backend to make it happen.
    vessel_list = interface.acquire_vessels(user, 50, 'wan')
    
    self.assertEqual(50, len(vessel_list))




  def test_acquire_lan_vessels_some_subnets_have_too_many_vessels_fail(self):
    """
    We're going to be trying to acquire 4 vessels in a single subnet. We'll
    make it so that there are 3 subnets to choose from. The first two will
    potentially have enough vessels for the user to satisfy their acquisition
    request, but too many vessels in each will fail. The third subnet tried
    will have enough succeed.
    """
    
    # We're going to have three subnets with 5 potential vessels each. We
    # want the first two subnets to fail. Choosing the values creatively
    # here is helped by knowing the logic of the function
    # vessels._acquire_vessels_from_list(). Basically, it won't try to
    # acquire more than the minumum needed at a time, so the first time
    # it loops it will try to acquire all 4, then the next time it loops
    # it will try to acquire however many of the 4 failed the first time.
    # It won't bother trying again if there are too few left in the list.
    results_1 = [False, True, True, True, False]
    results_2 = [False, False, True, True]
    results_3 = [False, True, True, True, True]
    calls_results = results_1 + results_2 + results_3
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    # Make sure the user starts with 10 credits.
    self.assertEqual(10, maindb.get_user_free_vessel_credits(user))
    
    # Create three subnets with 5 nodes each. We need to keep them all the same
    # size, otherwise we need to change the test to patch maindb so that the
    # subnets will be tried in the order we expect.
    testutil.create_nodes_on_same_subnet(5, [userport], ip_prefix="127.0.0.")
    testutil.create_nodes_on_same_subnet(5, [userport], ip_prefix="127.0.1.")
    testutil.create_nodes_on_same_subnet(5, [userport], ip_prefix="127.0.2.")
    
    # Now try to acquire 8 lan nodes on a single subnet.
    vessel_list = interface.acquire_vessels(user, 4, 'lan')
    
    self.assertEqual(4, len(vessel_list))
    
    # Make sure backend.acquire_vessel() got called the correct number of
    # times (that is, the call_results list got pop(0)'d enough times).
    self.assertEqual(0, len(calls_results))



  def test_acquire_specific_vessels(self):
    # 8 vessels will ultimately be acquired.
    calls_results = [True] * 8
    mocklib.mock_backend_acquire_vessel(calls_results)
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    userport = user.usable_vessel_port
    
    vesselcount = maindb.get_user_free_vessel_credits(user)
    
    # We use userport + 1 to make sure the user isn't being restricted to only
    # vessels that have their user port in their port list.
    testutil.create_nodes_on_different_subnets(vesselcount + 10, [userport + 1])
    
    vessels = list(maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(userport + 1))
    
    # Request the first 4 vessels in the list.
    first_vessel_list = interface.acquire_specific_vessels(user, vessels[:4])
    
    # Now request the first 6 vessels in the list. We should only get 2.
    second_vessel_list = interface.acquire_specific_vessels(user, vessels[:6])

    self.assertEqual(4, len(first_vessel_list))
    self.assertEqual(2, len(second_vessel_list))
    
    # Now ask for more vessels than the user has available, regardless of the
    # fact that some of the requested vessels aren't available.
    requestcount = vesselcount - 6 + 1
    
    func = interface.acquire_specific_vessels
    args = (user, vessels[:requestcount])
    self.assertRaises(InsufficientUserResourcesError, func, *args)





def run_test():
  unittest.main()



if __name__ == "__main__":
  run_test()
