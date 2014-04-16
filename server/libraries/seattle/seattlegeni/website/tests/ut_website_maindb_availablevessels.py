#pragma out
#pragma error OK

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

import unittest





next_nodeid_number = 0

def create_node_and_vessels_with_one_port_each(ip, portlist):
  
  global next_nodeid_number
  next_nodeid_number += 1
  
  nodeid = "node" + str(next_nodeid_number)
  port = 1234
  version = "10.0test"
  is_active = True
  owner_pubkey = "1 2"
  extra_vessel_name = "v1"
  
  node = maindb.create_node(nodeid, ip, port, version, is_active, owner_pubkey, extra_vessel_name)

  single_vessel_number = 2

  for vesselport in portlist:
    single_vessel_name = "v" + str(single_vessel_number)
    single_vessel_number += 1
    vessel = maindb.create_vessel(node, single_vessel_name)
    maindb.set_vessel_ports(vessel, [vesselport])
  
  return node





def create_nodes_on_same_subnet(count, portlist_for_vessels_on_each_node):
  # Create 'count' nodes on the same subnet and on each node create a vessel
  # with a single port for each port in 'portlist_for_vessels_on_each_node'.
  ip_prefix = "ip = 127.0.0."
  for i in range(count):
    ip = ip_prefix + str(i)
    create_node_and_vessels_with_one_port_each(ip, portlist_for_vessels_on_each_node)





def create_nodes_on_different_subnets(count, portlist_for_vessels_on_each_node):
  # Create 'count' nodes on different subnets and on each node create a vessel
  # with a single port for each port in 'portlist_for_vessels_on_each_node'.
  ip_prefix = "127.1."
  ip_suffix = ".0"
  for i in range(count):
    ip = ip_prefix + str(i) + ip_suffix
    create_node_and_vessels_with_one_port_each(ip, portlist_for_vessels_on_each_node)





def create_nat_nodes(count, portlist_for_vessels_on_each_node):
  # Create 'count' nat nodes and on each node create a vessel
  # with a single port for each port in 'portlist_for_vessels_on_each_node'.
  ip_prefix = maindb.NAT_STRING_PREFIX
  for i in range(count):
    ip = ip_prefix + str(i)
    create_node_and_vessels_with_one_port_each(ip, portlist_for_vessels_on_each_node)





def _get_queryset_include_nat(port): 
  """
  Give a nicer though less accurate name to the function as we're using it a
  lot here in the tests.
  """
  return maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(port)





def _get_queryset_exclude_nat(port):
  """
  Give a nicer though less accurate name to the function as we're using it a
  lot here in the tests.
  """
  return maindb._get_queryset_of_all_available_vessels_for_a_port_exclude_nat_nodes(port)





def _get_queryset_only_nat(port): 
  """
  Give a nicer though less accurate name to the function as we're using it a
  lot here in the tests.
  """
  return maindb._get_queryset_of_all_available_vessels_for_a_port_only_nat_nodes(port)





class SeattleGeniTestCase(unittest.TestCase):


  def setUp(self):
    # Setup a fresh database for each test.
    testlib.setup_test_db()



  def tearDown(self):
    # Cleanup the test database.
    testlib.teardown_test_db()


  def test_get_queryset_1(self):
    """
    This is ultimately testing
    maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes()
    """
    
    userport = 100
    
    # Make sure the queryset is initially empty.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(0, queryset.count())

    # Create a node that has no vessels.
    ip = "127.0.0.1"
    portlist = []
    create_node_and_vessels_with_one_port_each(ip, portlist)
    
    # Make sure the queryset is still empty.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(0, queryset.count())
    
    # Create a node that has one vessel, but not on this user's port.
    ip = "127.0.0.2"
    portlist = [userport + 1]
    create_node_and_vessels_with_one_port_each(ip, portlist)
    
    # Make sure the queryset is still empty.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(0, queryset.count())
    
    # Create a node that has one vessel that is on the user's port
    ip = "127.0.0.3"
    portlist = [userport]
    create_node_and_vessels_with_one_port_each(ip, portlist)
    
    # We expect one available vessel.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    
    # Make sure the vessel is on the last node we created.
    availablevessel = list(queryset)[0]
    self.assertEqual("127.0.0.3", availablevessel.node.last_known_ip)
    
    
    
  def test_get_queryset_node_is_active_changes(self):
    """
    This is ultimately testing
    maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes()
    """
    
    userport = 100
    
    # Create a node that has three vessels but only one vessel on the user's port.
    ip = "127.0.0.1"
    portlist = [userport - 1, userport, userport + 1]
    node = create_node_and_vessels_with_one_port_each(ip, portlist)
    
    # We expect one available vessel.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    
    # Now update the node to mark it as inactive.
    node.is_active = False
    node.save()
    
    # We expect zero available vessels.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(0, queryset.count())
    
    # Now update the node to mark it as active again.
    node.is_active = True
    node.save()
    
    # We expect one available vessel.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())



  def test_get_queryset_node_is_broken_changes(self):
    """
    This is ultimately testing
    maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes()
    """
    
    userport = 100
    
    # Create a node that has three vessels but only one vessel on the user's port.
    ip = "127.0.0.1"
    portlist = [userport - 1, userport, userport + 1]
    node = create_node_and_vessels_with_one_port_each(ip, portlist)
    
    # We expect one available vessel.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    
    # Now update the node to mark it as inactive.
    node.is_broken = True
    node.save()
    
    # We expect zero available vessels.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(0, queryset.count())
    
    # Now update the node to mark it as active again.
    node.is_broken = False
    node.save()
    
    # We expect one available vessel.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())


    
  def test_get_queryset_vessel_is_dirty_changes(self):
    """
    This is ultimately testing
    maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes()
    """
    
    userport = 100
    
    # Create two nodes that have three vessels but only one vessel on the user's port.
    portlist = [userport - 1, userport, userport + 1]
    ip = "127.0.0.1"
    create_node_and_vessels_with_one_port_each(ip, portlist)
    ip = "127.0.0.2"
    create_node_and_vessels_with_one_port_each(ip, portlist)

    # We expect two available vessels.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(2, queryset.count())
    
    # Now mark one of the two available vessels as dirty.
    vessel = queryset[0]
    vessel.is_dirty = True
    vessel.save()
    
    # We expect one available vessel, and it shouldn't be the dirty one.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    self.assertNotEqual(vessel, queryset[0])
    
    

  def test_get_queryset_vessel_acquired_by_user_changes(self):
    """
    This is ultimately testing
    maindb._get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes()
    """
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    userport = user.usable_vessel_port
    
    # Create two nodes that have three vessels but only one vessel on the user's port.
    portlist = [userport - 1, userport, userport + 1]
    ip = "127.0.0.1"
    create_node_and_vessels_with_one_port_each(ip, portlist)
    ip = "127.0.0.2"
    create_node_and_vessels_with_one_port_each(ip, portlist)

    # We expect two available vessels.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(2, queryset.count())
    
    # Mark one of the vessels as acquired.
    vessel = queryset[0]
    maindb.record_acquired_vessel(user, vessel)
    
    # We expect one available vessel, and it shouldn't be the acquired one.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    self.assertNotEqual(vessel, queryset[0])
    
    # Release the vessel. It should still be dirty.
    maindb.record_released_vessel(vessel)
    
    # We expect one available vessel, and it shouldn't be the acquired one.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(1, queryset.count())
    self.assertNotEqual(vessel, queryset[0])
    
    # Mark the vessel as clean (as if the backend cleaned it up).
    maindb.mark_vessel_as_clean(vessel)
    
    # We expect two available vessels.
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(2, queryset.count())
    

    
# TODO: add a test for broken nodes if/when an is_broken flag is added to nodes



  def test_get_queryset_different_node_types(self):
    
    userport = 12345
    
    # We choose the numbers of each type of node in a way that helps ensure
    # that we don't accidentally pass the test if something is going wrong.
    
    # We will get one vessel on each created node for each port in portlist
    # and there will be only that one port on the vessel.
    portlist = [userport - 1, userport, userport + 1]
    
    create_nodes_on_same_subnet(3, portlist)
    create_nodes_on_different_subnets(7, portlist)
    create_nat_nodes(13, portlist)

    # We expect 23 available total vessels (that is, one vessel on each node).
    queryset = _get_queryset_include_nat(userport)
    self.assertEqual(23, queryset.count())
    
    # We expect 10 available vessels not on nat nodes.
    queryset = _get_queryset_exclude_nat(userport)
    self.assertEqual(10, queryset.count())
    
    # We expect 13 available vessels on nat nodes.
    queryset = _get_queryset_only_nat(userport)
    self.assertEqual(13, queryset.count())




  def test_get_available_rand_vessels(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    userport = user.usable_vessel_port
    
    # We choose the numbers of each type of node in a way that helps ensure
    # that we don't accidentally pass the test if something is going wrong.
    
    # We will get one vessel on each created node for each port in portlist
    # and there will be only that one port on the vessel.
    portlist = [userport - 1, userport, userport + 1]
    
    create_nodes_on_same_subnet(3, portlist)
    create_nodes_on_different_subnets(7, portlist)
    create_nat_nodes(13, portlist)
      
    # Request 0 vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_rand_vessels, user, 0)
    
    # Request a negative number of vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_rand_vessels, user, -1)
    
    # We expect there to be 23 available rand vessels (one vessel on each node
    # including the nat nodes).
    
    # Request 1 vessel, make sure we get back more than 1 potential vessels.
    vessel_list = maindb.get_available_rand_vessels(user, 1)
    self.assertTrue(len(vessel_list) > 1)
      
    # Request 5 vessels, make sure we get back more than 5 potential vessels.
    vessel_list = maindb.get_available_rand_vessels(user, 5)
    self.assertTrue(len(vessel_list) > 5)
      
    # Request 23 vessels, make sure we get back all 23 vessels we expect.
    vessel_list = maindb.get_available_rand_vessels(user, 23)
    self.assertEqual(23, len(vessel_list))
    
    # Request 24 vessels, make sure we get an exception.
    self.assertRaises(UnableToAcquireResourcesError, maindb.get_available_rand_vessels, user, 24)

      
      
  def test_get_available_wan_vessels(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    userport = user.usable_vessel_port
    
    # We choose the numbers of each type of node in a way that helps ensure
    # that we don't accidentally pass the test if something is going wrong.
    
    # We will get one vessel on each created node for each port in portlist
    # and there will be only that one port on the vessel.
    portlist = [userport - 1, userport, userport + 1]
    
    create_nodes_on_same_subnet(3, portlist)
    create_nodes_on_different_subnets(7, portlist)
    create_nat_nodes(13, portlist)
      
    # Request 0 vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_wan_vessels, user, 0)
    
    # Request a negative number of vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_wan_vessels, user, -1)
    
    # We expect there to be 8 available rand vessels (one vessel on each node
    # non-nat node on each subnet, and there are 8 subnets).
    
    # Request 1 vessel, make sure we get back more than 1 potential vessels.
    vessel_list = maindb.get_available_wan_vessels(user, 1)
    self.assertTrue(len(vessel_list) > 1)
      
    # Request 5 vessels, make sure we get back more than 5 potential vessels.
    vessel_list = maindb.get_available_wan_vessels(user, 5)
    self.assertTrue(len(vessel_list) > 5)
      
    # Request 8 vessels, make sure we get back all 8 vessels we expect.
    vessel_list = maindb.get_available_wan_vessels(user, 8)
    self.assertEqual(8, len(vessel_list))
    
    # Request 9 vessels, make sure we get an exception.
    self.assertRaises(UnableToAcquireResourcesError, maindb.get_available_wan_vessels, user, 9)

      
      
  def test_get_available_nat_vessels(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    userport = user.usable_vessel_port
    
    # We choose the numbers of each type of node in a way that helps ensure
    # that we don't accidentally pass the test if something is going wrong.
    
    # We will get one vessel on each created node for each port in portlist
    # and there will be only that one port on the vessel.
    portlist = [userport - 1, userport, userport + 1]
    
    create_nodes_on_same_subnet(3, portlist)
    create_nodes_on_different_subnets(7, portlist)
    create_nat_nodes(13, portlist)
      
    # Request 0 vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_nat_vessels, user, 0)
    
    # Request a negative number of vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_nat_vessels, user, -1)
    
    # We expect there to be 13 available nat vessels (one vessel on each node
    # nat node).
    
    # Request 1 vessel, make sure we get back more than 1 potential vessels.
    vessel_list = maindb.get_available_nat_vessels(user, 1)
    self.assertTrue(len(vessel_list) > 1)
      
    # Request 5 vessels, make sure we get back more than 5 potential vessels.
    vessel_list = maindb.get_available_nat_vessels(user, 5)
    self.assertTrue(len(vessel_list) > 5)
      
    # Request 13 vessels, make sure we get back all 13 vessels we expect.
    vessel_list = maindb.get_available_nat_vessels(user, 13)
    self.assertEqual(13, len(vessel_list))
    
    # Request 14 vessels, make sure we get an exception.
    self.assertRaises(UnableToAcquireResourcesError, maindb.get_available_nat_vessels, user, 14)



  def test_get_available_lan_vessels_by_subnet(self):
    
    # Create a user who will be doing the acquiring.
    user = maindb.create_user("testuser", "password", "example@example.com", "affiliation", "1 2", "2 2 2", "3 4")
    
    userport = user.usable_vessel_port
    
    # We choose the numbers of each type of node in a way that helps ensure
    # that we don't accidentally pass the test if something is going wrong.
    
    # We will get one vessel on each created node for each port in portlist
    # and there will be only that one port on the vessel.
    portlist = [userport - 1, userport, userport + 1]
    
    create_nodes_on_same_subnet(29, portlist)
    create_nodes_on_different_subnets(7, portlist)
    create_nat_nodes(13, portlist)
    
    # Request 0 vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_lan_vessels_by_subnet, user, 0)
    
    # Request a negative number of vessels, make sure it raises a AssertionError.
    self.assertRaises(AssertionError, maindb.get_available_lan_vessels_by_subnet, user, -1)
    
    # We expect there to be 7 subnets with a single available vessel for the
    # user (the 7 on differnt subnets created above) and 1 subnet with 29
    # available vessels for the user (the 29 nodes on the same subnet created
    # above).
    
    # Request 1 vessel, make sure we get back a list of 8 subnets where one
    # subnet has more than one available vessel and the other 7 have only
    # one available vessel.
    subnet_vessel_list = maindb.get_available_lan_vessels_by_subnet(user, 1)
    self.assertEqual(8, len(subnet_vessel_list))
    
    vessel_list_sizes = []
    for vessel_list in subnet_vessel_list:
      vessel_list_sizes.append(len(vessel_list))
    vessel_list_sizes.sort()
    
    self.assertEqual([1, 1, 1, 1, 1, 1, 1], vessel_list_sizes[:7])
    self.assertTrue(vessel_list_sizes[7] > 1)
      
    # Request 5 vessels, make sure we get back a list that has one subnet and
    # in that subnet is a list of more than 5 potential vessels.
    subnet_vessel_list = maindb.get_available_lan_vessels_by_subnet(user, 5)
    self.assertEqual(1, len(subnet_vessel_list))
    self.assertTrue(len(subnet_vessel_list[0]) > 5)
      
    # Request 29 vessels, make sure we get back a list that has one subnet and
    # in that subnet is a list of 29 potential vessels.
    subnet_vessel_list = maindb.get_available_lan_vessels_by_subnet(user, 29)
    self.assertEqual(1, len(subnet_vessel_list))
    self.assertEqual(29, len(subnet_vessel_list[0]))
    
    # Request 30 vessels, make sure we get an exception.
    self.assertRaises(UnableToAcquireResourcesError, maindb.get_available_lan_vessels_by_subnet, user, 30)





def run_test():
  unittest.main()



if __name__ == "__main__":
  run_test()
