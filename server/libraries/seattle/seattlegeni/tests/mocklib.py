"""
<Program>
  mocklib.py
  
<Author>
  Justin Samuel

<Date Started>
  Aug 10, 2009
  
<Purpose>
  This provides functions that take care of mocking out (read: monkey
  patching) various parts of seattlegeni's internal api, including calls to:

    nodemanager.get_node_info
    lockserver.create_lockserver_handle
    lockserver.destroy_lockserver_handle
    lockserver._perform_lock_request
    backend.acquire_vessel
    backend.generate_key
    keygen.generate_keypair
    
  The idea is to use the functions provided in this module to keep test scripts
  clean and not repeat code in each one doing the same or similar monkey
  patching with mock versions of these function calls.
"""

from seattlegeni.common.api import backend
from seattlegeni.common.api import keygen
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import nodemanager

from seattlegeni.common.exceptions import *



_mock_nodemanager_get_node_info_args = None

def _mock_get_node_info(ip, port):
  
  (nodeid_key, version, vessels_dict) = _mock_nodemanager_get_node_info_args
  nodeinfo = {"version" : version,
              "nodename" : "",
              "nodekey" : nodeid_key,
              "vessels" : {}}
  nodeinfo["vessels"] = vessels_dict
  return nodeinfo

def mock_nodemanager_get_node_info(nodeid_key, version, vessels_dict):
  global _mock_nodemanager_get_node_info_args
  _mock_nodemanager_get_node_info_args = (nodeid_key, version, vessels_dict)
  nodemanager.get_node_info = _mock_get_node_info






def _mock_create_lockserver_handle(lockserver_url=None):
  pass

def _mock_destroy_lockserver_handle(lockserver_handle):
  pass

def _mock_perform_lock_request(request_type, lockserver_handle, user_list=None, node_list=None):
  pass

def mock_lockserver_calls():
  
  lockserver.create_lockserver_handle = _mock_create_lockserver_handle
  lockserver.destroy_lockserver_handle = _mock_destroy_lockserver_handle
  lockserver._perform_lock_request = _mock_perform_lock_request





_mock_acquire_vessel_result_list = None

def _mock_acquire_vessel(geniuser, vessel):
  
  result_list = _mock_acquire_vessel_result_list
  
  if len(result_list) == 0:
    raise Exception("_mock_acquire_vessel ran out results. " + 
                    "Either you need to provide more results in the result_list, " + 
                    "or this is a legitimate test failure.")
  if result_list.pop(0):
    pass
  else:
    raise UnableToAcquireResourcesError

def mock_backend_acquire_vessel(result_list):
  """
  Provide a list of boolean values that the mock'd out backend.acquire_vessels
  will use to decide whether to return without an exception (True) or to raise
  an UnableToAcquireResourcesError (False). The list will be used in order and
  an exception will be raised if the mock backend.acquire_vessel() function is
  called more times than there are items in the list.
  """
  global _mock_acquire_vessel_result_list
  _mock_acquire_vessel_result_list = result_list
  backend.acquire_vessel = _mock_acquire_vessel





_mock_generate_key_keylist = None

def _mock_generate_key(keydescription):
  keylist = _mock_generate_key_keylist
  
  if len(keylist) == 0:
    raise Exception("_mock_generate_key ran out of keys. " + 
                    "Either you need to provide more keys, or this is a legitimate test failure.")
  return keylist.pop(0)

def mock_backend_generate_key(keylist):
  global _mock_generate_key_keylist
  _mock_generate_key_keylist = keylist
  backend.generate_key = _mock_generate_key





_mock_generate_keypair_keypairlist = None

def _mock_generate_keypair():
  keypairlist = _mock_generate_keypair_keypairlist
  
  if len(keypairlist) == 0:
    raise Exception("_mock_generate_keypair ran out of keypairs. " + 
                    "Either you need to provide more keypairs, or this is a legitimate test failure.")
  return keypairlist.pop(0)

def mock_keygen_generate_keypair(keypairlist):
  global _mock_generate_keypair_keypairlist
  _mock_generate_keypair_keypairlist = keypairlist
  keygen.generate_keypair = _mock_generate_keypair

