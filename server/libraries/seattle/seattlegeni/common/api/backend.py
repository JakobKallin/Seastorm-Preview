"""
<Program>
  backend.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is the API that should be used to interact with the backend XML-RPC
  server. Functions in this module are the only way that other code should
  interact with the backend.
   
  All components of seattlegeni use the backend to perform any nodemanager
  communication that changes the state of a node. ("State" here means
  modifying the node in any way, not "state" as in the "canonical state".)
  If the node only needs to be queried, not modified, then that can be
  done directly using the nodemanager api. This prevents the backend from
  needing to be called for regular querying done by polling daemons yet
  keeps the backend as the sole place where node changing operations
  are performed.
   
  The website uses only four functions in this module:
    acquire_vessel()
    release_vessel()
    generate_key()
    set_vessel_users()
     
  The other functions are used by polling daemons. In order to use the other
  functions, set_backend_authcode() must be called by the script first.
  
  Note that the none of these function calls will result in changes to the
  database. Any corresponding changes that also need to be made in the
  database must be made by any client code that uses this api.
"""

import socket
import traceback
import xmlrpclib

from seattlegeni.common.exceptions import *

from seattlegeni.common.util.decorators import log_function_call





BACKEND_URL = "http://127.0.0.1:8020"

# This is not a thread-local variable. There isn't any case where one thread
# in a process will have this authcode and another won't. So, we don't make
# the client code pass around a handle just for this.
backend_authcode = None





def _get_backend_proxy():
  return xmlrpclib.ServerProxy(BACKEND_URL)





def _do_backend_request(func, *args):
  try:
    return func(*args)
  except xmlrpclib.Fault, fault:
    if fault.faultCode == 100:
      raise NodemanagerCommunicationError(fault.faultString)
    else:
      raise ProgrammerError("The backend rejected the request: " + traceback.format_exc())
  except xmlrpclib.ProtocolError:
    raise InternalError("Unable to communicate with the backend: " + traceback.format_exc())
  except socket.error:
    raise InternalError("Unable to communicate with the backend: " + traceback.format_exc())






def _require_backend_authcode():
  if backend_authcode is None:
    raise ProgrammerError("You must call set_backend_authcode(authcode) before calling this function.")





# Not using log_function_call so we don't log the authcode.
def set_backend_authcode(authcode):
  """
  <Purpose>
    Sets the value of the authcode sent to the backend with privileged requests.
    This is needed for the backend to ensure that calls to the privileged
    operations (set_vessel_owner, split_vessel, join_vessel) are allowed.
    The website will never need to use this function (and shouldn't have
    access to a valid authcode, either). This function will need to be used
    by polling daemons such as node state transition scripts.
  <Arguments>
    authcode
      The authcode to send with privileged requests.
  <Exceptions>
    None
  <Side Effects>
    The value of the global variable backend_authcode has been changed.
  <Returns>
    None
  """
  global backend_authcode
  backend_authcode = authcode





@log_function_call
def acquire_vessel(geniuser, vessel):
  """
  <Purpose>
    Perform the necessary nodemanager communication to acquire a vessel for a
    user.
  <Arguments>
    geniuser
      The user the vessel is to be acquired for.
    vessel
      A Vessel object of the vessel to be acquired.
  <Exceptions>
    None
  <Side Effects>
    The vessel has been acquired for the user.
  <Returns>
    None
  """
  # Acquiring a vessel is just setting the userkeylist to include only this
  # user's key.
  func = _get_backend_proxy().SetVesselUsers
  args = (vessel.node.node_identifier, vessel.name, [geniuser.user_pubkey])
  
  try:
    _do_backend_request(func, *args)
  except NodemanagerCommunicationError:
    raise UnableToAcquireResourcesError





@log_function_call
def release_vessel(vessel):
  """
  <Purpose>
    Perform the necessary nodemanager communication to release a vessel.
  <Arguments>
    vessel
      A Vessel object of an acquired vessel to be released.
  <Exceptions>
    None
  <Side Effects>
    The vessel has been released (at least as far as the client code is
    concerned).
  <Returns>
    None
  """
  # This is actually a noop. The reason for this is because the backend doesn't
  # perform immediate action because of a released vessel. Instead, the client
  # code will user maindb.record_released_vessel() and the database change
  # resulting from that will cause the cleanup thread in the backend to do
  # anything it needs to do.
  pass





@log_function_call
def generate_key(keydecription):
  """
  <Purpose>
    Generate a new key pair through the backend. The backend will store the
    private key in the keydb. As of the time of writing this, this method
    is mainly to be used by the website to obtain a donor_pubkey without
    ever having to see the corresponding private key.
  <Arguments>
    keydecription
      A description of what this key is for. This should be specific enough
      to locate where the returned public key is stored in the maindb.
  <Exceptions>
    None
  <Side Effects>
    A new key has been generated and stored in the the keydb with the privided
    description.
  <Returns>
    The public key part of the key pair. The key is in string format.
  """
  func = _get_backend_proxy().GenerateKey
  args = (keydecription,)
  
  return _do_backend_request(func, *args)





@log_function_call
def set_vessel_user_keylist(node, vesselname, userkeylist):
  """
  <Purpose>
    Perform the necessary nodemanager communication to set the user key list
    for a vessel.
  <Arguments>
    node
      The Node object of the node which the vessel is on.
    vesselname
      The name of the vessel whose user key list is to be set.
    userkeylist
      A list of public key strings that are the user keys to be set for the vessel.
  <Exceptions>
    NodemanagerCommunicationError
      If there's a problem communicating with the node.
  <Side Effects>
    The user key list for the vessel has been changed on the vessel.
  <Returns>
    None
  """
  func = _get_backend_proxy().SetVesselUsers
  args = (node.node_identifier, vesselname, userkeylist)
  
  _do_backend_request(func, *args)





@log_function_call
def set_vessel_owner_key(node, vesselname, old_ownerkey, new_ownerkey):
  """
  <Purpose>
    Perform the necessary nodemanager communication to set the owner key
    for a vessel.
  <Arguments>
    node
      The Node object of the node which the vessel is on.
    vesselname
      The name of the vessel whose owner key is to be set.
    old_ownerkey
      A public key string of the owner key that is the current owner key for
      the vessel. Note that this key (with its correspond private key) must
      already exist in the keydb before this function is called.
    new_ownerkey
      A public key string of the owner key to be set for the vessel. Note that
      this key (with its correspond private key) must already exist in the
      keydb before this function is called.
  <Exceptions>
    NodemanagerCommunicationError
      If there's a problem communicating with the node.
  <Side Effects>
    The owner key on the vessel has been changed. The main database is not modified.
  <Returns>
    None
  """
  # Changing the owner key is a privileged request and the backend server will
  # require an authcode to be sent with the request.
  _require_backend_authcode()

  func = _get_backend_proxy().SetVesselOwner
  args = (backend_authcode, node.node_identifier, vesselname, old_ownerkey, new_ownerkey)
  
  _do_backend_request(func, *args)

  



@log_function_call
def split_vessel(node, vesselname, desiredresourcedata):
  """
  <Purpose>
    Perform the necessary nodemanager communication to split the vessel.
  <Arguments>
    node
      The Node object of the node which the vessel is on.
    vesselname
      The name of the vessel that is to be split.
    desiredresourcedata
      A string of resourcedata that specifies the resources of a new vessel to
      create when splitting the existing vessel. This resourcedata has the
      format of a resources file.
  <Exceptions>
    InvalidRequestError
      If unable to split the vessel. This includes if it fails because there
      aren't enough resources available to do the split.
    NodemanagerCommunicationError
      If there's a problem communicating with the node.
  <Side Effects>
    The vessel passed in as an argument to the function no longer exists.
    It has been split into two new vessels, one of which has the resources
    specified in the desiredresourcedata. The main database is not modified.
  <Returns>
    A tuple of the two new vessel names that resulted from the split. The
    first element of the tuple is the name of the vessel that has the
    leftover resources from the split. The second element of the tuple is
    the name of the vessel that has the exact resources specified in the
    desiredresourcedata.
  """
  # Splitting a vessel is a privileged request and the backend server will
  # require an authcode to be sent with the request.
  _require_backend_authcode()
  
  func = _get_backend_proxy().SplitVessel
  args = (backend_authcode, node.node_identifier, vesselname, desiredresourcedata)
  
  # We don't have a great way of having the backend tell us that the split
  # failed only due to lacking resources and not because of some other type
  # of problem. So, we're going to have to assume that all failures in this
  # call are because of not enough resources to do the split.
  try:
    return _do_backend_request(func, *args)
  except ProgrammerError, e:
    # The exception message will already contain the traceback info because
    # of the message that was set when the ProgrammerError was thrown in
    # the call to _do_backend_request().
    raise InvalidRequestError(str(e))





@log_function_call
def join_vessels(node, firstvesselname, secondvesselname):
  """
  <Purpose>
    Perform the necessary nodemanager communication to join the vessels.
  <Arguments>
    node
      The Node object of the node which the vessels are on.
    firstvesselname
      The name of the first vessel that is to be joined.
    secondvesselname
      The name of the second vessel that is to be joined.
  <Exceptions>
    NodemanagerCommunicationError
      If there's a problem communicating with the node.
  <Side Effects>
    The two vessel passed in as arguments to the function no longer exist.
    They have been joined into a new vessel. The first vessel will retain the
    user keys and therefore the state. The main database is not modified.
  <Returns>
    The name of the new vessel that has been created by joining together the
    two vessels.
  """
  # Joining two vessels is a privileged request and the backend server will
  # require an authcode to be sent with the request.
  _require_backend_authcode()
  
  func = _get_backend_proxy().JoinVessels
  args = (backend_authcode, node.node_identifier, firstvesselname, secondvesselname)
  
  return _do_backend_request(func, *args)
  
