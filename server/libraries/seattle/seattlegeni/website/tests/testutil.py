"""
Utility functions for the test scripts in this directory/package.
"""

# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.common.api import maindb





next_nodeid_number = 0

def create_node_and_vessels_with_one_port_each(ip, portlist, is_active=True):
  
  global next_nodeid_number
  next_nodeid_number += 1
  
  nodeid = "node" + str(next_nodeid_number)
  port = 1234
  version = "10.0test"
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





def create_nodes_on_same_subnet(count, portlist_for_vessels_on_each_node, ip_prefix="127.0.0."):
  # Create 'count' nodes on the same subnet and on each node create a vessel
  # with a single port for each port in 'portlist_for_vessels_on_each_node'.
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

