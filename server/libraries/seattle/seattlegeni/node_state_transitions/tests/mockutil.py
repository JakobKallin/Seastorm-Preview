
# The seattlegeni testlib must be imported first. We do this in case this
# module gets executed as a test to prevent it from "failing".
from seattlegeni.tests import testlib

import random

from seattlegeni.common.api import backend
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import nodemanager
from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

from seattlegeni.node_state_transitions import node_transition_lib

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")




testusername = "testuser"

node_ip = "127.0.0.1"
node_port = 1224
node_address = node_ip + ":" + str(node_port)

nodeid_key = {"e" : 1, "n" : 2}
nodeid_key_str = str(nodeid_key["e"]) + " " + str(nodeid_key["n"])

donor_key = {"e" : 3, "n" : 4}
donor_key_str = str(donor_key["e"]) + " " + str(donor_key["n"])

per_node_key = {"e" : 5, "n" : 6}
per_node_key_str = str(per_node_key["e"]) + " " + str(per_node_key["n"])

extra_vessel_name = "v1"

def mockutil_cleanup_variables():
  global testusername
  global node_ip
  global node_port
  global node_address
  global nodeid_key
  global nodeid_key_str
  global donor_key
  global donor_key_str
  global per_node_key
  global per_node_key_str
  global extra_vessel_name

  testusername = "testuser"

  node_ip = "127.0.0.1"
  node_port = 1224
  node_address = node_ip + ":" + str(node_port)

  nodeid_key = {"e" : 1, "n" : 2}
  nodeid_key_str = str(nodeid_key["e"]) + " " + str(nodeid_key["n"])

  donor_key = {"e" : 3, "n" : 4}
  donor_key_str = str(donor_key["e"]) + " " + str(donor_key["n"])

  per_node_key = {"e" : 5, "n" : 6}
  per_node_key_str = str(per_node_key["e"]) + " " + str(per_node_key["n"])

  extra_vessel_name = "v1"

def mock_transitionlib_do_advertise_lookup(nodeaddress_list_to_return):
  
  def _mock_do_advertise_lookup(state):
    return nodeaddress_list_to_return
  
  node_transition_lib._do_advertise_lookup = _mock_do_advertise_lookup





def mock_nodemanager_get_node_info(nodeid_key, version, vessels_dict):
  
  def _mock_get_node_info(ip, port):
    nodeinfo = {"version" : version,
                "nodename" : "",
                "nodekey" : nodeid_key,
                "vessels" : {}}
    nodeinfo["vessels"] = vessels_dict
    return nodeinfo
  
  nodemanager.get_node_info = _mock_get_node_info





def mock_lockserver_calls():
  
  def _mock_create_lockserver_handle(lockserver_url=None):
    pass
  lockserver.create_lockserver_handle = _mock_create_lockserver_handle
  
  def _mock_destroy_lockserver_handle(lockserver_handle):
    pass
  lockserver.destroy_lockserver_handle = _mock_destroy_lockserver_handle
  
  def _mock_perform_lock_request(request_type, lockserver_handle, user_list=None, node_list=None):
    pass
  lockserver._perform_lock_request = _mock_perform_lock_request




def mock_backend_generate_key(keylist):

  def _mock_generate_key(keydescription):
    return keylist.pop()
  
  backend.generate_key = _mock_generate_key



def mock_nodemanager_get_vesselresources():
  
  def _mock_get_vessel_resources(*args):
    resource_dict={}
    resourcelist = []
    #generate resource list
    for i in range(90):
      resourcelist.append(i)
    resource_dict['usableports'] = resourcelist
    
    return resource_dict

  nodemanager.get_vessel_resources = _mock_get_vessel_resources




# How many times backend.set_vessel_owner_key() has been called.
set_vessel_owner_key_call_count = 0

def mock_backend_set_vessel_owner_key():

  global set_vessel_owner_key_call_count

  def _mock_set_vessel_owner_key(node, vesselname, old_ownerkey, new_ownerkey):

    global set_vessel_owner_key_call_count

    print "[_mock_set_vessel_owner_key] called: ", node, vesselname, old_ownerkey, new_ownerkey

    # We changed things so that the node will now be inactive until the node
    # is changed to the onepercentmanyevents state.
    #assert(node == maindb.get_active_nodes()[0])
    assert(vesselname == extra_vessel_name)
    assert(old_ownerkey == donor_key_str)
    assert(new_ownerkey == per_node_key_str)

    set_vessel_owner_key_call_count += 1
  
  set_vessel_owner_key_call_count = 0

  backend.set_vessel_owner_key = _mock_set_vessel_owner_key




# How many times backend.set_vessel_user_keylist() has been called.
set_vessel_user_keylist_call_count = 0

def mock_backend_set_vessel_user_keylist(expected_key_list):

  global set_vessel_user_keylist_call_count

  def _mock_set_vessel_user_keylist(node, vesselname, userkeylist):

    global set_vessel_user_keylist_call_count

    print "[_mock_set_vessel_user_keylist] called: ", node, vesselname, userkeylist

    # We changed things so that the node will now be inactive until the node
    # is changed to the onepercentmanyevents state.
    #assert(node == maindb.get_active_nodes()[0])

    # Make sure that the name of the vessel is correct, if we are setting
    # the keylist for the extra vessel.

    if userkeylist != []:
      assert(vesselname == extra_vessel_name)

    assert(userkeylist == expected_key_list or userkeylist == [])

    set_vessel_user_keylist_call_count += 1

  set_vessel_user_keylist_call_count = 0

  backend.set_vessel_user_keylist = _mock_set_vessel_user_keylist




#How many times backend.split_vessel() has been called
split_vessel_call_count = 0

def mock_backend_split_vessel():

  global split_vessel_call_count

  def _mock_split_vessel(node, vesselname, resource_data):

    global split_vessel_call_count
    global extra_vessel_name

    print "[_mock_split_vessel] called: ", node, vesselname, resource_data

    # We changed things so that the node will now be inactive until the node
    # is changed to the onepercentmanyevents state.
    #assert(node == maindb.get_active_nodes()[0])
    assert(vesselname == extra_vessel_name)

    split_vessel_call_count += 1
    extra_vessel_name = "extra_vessel_split"+str(split_vessel_call_count)
    return ("extra_vessel_split"+str(split_vessel_call_count), 
            "new_vessel"+str(split_vessel_call_count))

  split_vessel_call_count = 0

  backend.split_vessel = _mock_split_vessel




#How many times backend.join_vessels() has been called
join_vessels_call_count = 0

def mock_backend_join_vessels():

  global join_vessels_call_count

  def _mock_join_vessels(node, extra_vesselname, other_vesselname):

    global join_vessels_call_count
    global extra_vessel_name

    print "[_mock_join_vessels] called: ", node, extra_vesselname, other_vesselname

    # We changed things so that the node will now be inactive until the node
    # is changed to the onepercentmanyevents state.
    #assert(node == maindb.get_active_nodes()[0])
    assert(extra_vesselname == extra_vessel_name)

    join_vessels_call_count += 1

    extra_vessel_name = "extra_vessel_join"+str(join_vessels_call_count)

    return extra_vessel_name

  join_vessels_call_count = 0

  backend.join_vessels = _mock_join_vessels




#mock up for pubkey to string
def _mock_pubkey_to_string(pubkey):
  pub_string = str(pubkey['e'])+" "+str(pubkey['n'])
  return pub_string

node_transition_lib._do_rsa_publickey_to_string = _mock_pubkey_to_string
