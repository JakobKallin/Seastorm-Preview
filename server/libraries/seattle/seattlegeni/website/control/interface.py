"""
<Program Name>
  interface.py

<Started>
  June 17, 2009

<Author>
  Justin Samuel

<Purpose>
  This module presents the only methods that a frontend action will call. These
  methods do the work of ensuring that an action requested through a frontend
  are performed. The resulting data that the frontend needs is returned from
  these methods.
  
  This module should be the only point of entry from a frontend to the rest of
  the code base.

  Functions in this module will make calls to the following APIs:
    * backend
    * keygen
    * lockserver
    * maindb
  
<Notes>
  * All references to user here are to our GeniUser model, not to the django user.
  
  * The functions that modify the seattlegeni database or perform actions on
    nodes all do an extra check to ensure the user is valid after obtaining a
    user lock. This is to ensure that user has not been deleted and to see other
    changes to the user that were made between the time that the request was
    made and when the lock was obtained.
    
  * When using this module from the frontend views, you do not need to catch
    InternalError, ProgrammerError, or otherwise uncaught exceptions. Those
    are allowed to trickle all the way up and get handled based on how we've
    configured django.
"""

import traceback
import datetime

import django.contrib.auth

from seattlegeni.common.exceptions import *

from seattlegeni.common.api import backend
from seattlegeni.common.api import keygen
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb

from seattlegeni.common.util import validations

from seattlegeni.common.util.assertions import *

from seattlegeni.common.util.action_log_decorators import log_action

from seattlegeni.common.util.decorators import log_function_call
from seattlegeni.common.util.decorators import log_function_call_and_only_first_argument
from seattlegeni.common.util.decorators import log_function_call_without_arguments
from seattlegeni.common.util.decorators import log_function_call_without_return

from seattlegeni.website.control import vessels





@log_function_call_and_only_first_argument
def register_user(username, password, email, affiliation, pubkey=None):
  """
  <Purpose>
    Creates a user record with the specified information and sets any additional
    information necessary for the user record to be complete.
  <Arguments>
    username
    password
    email
    affiliation
    pubkey
      Optional. A string. If not provided, a key pair will be generated for this user.
  <Exceptions>
    UsernameAlreadyExistsError
      If there is already a user with the specified username.
    ValidationError
      If any of the arguments contains invalid values or if the username is the
      same as the password.
  <Side Effects>
    The user record in the django db is created as well as a user record in the
    corresponding user profile table that stores our custom information. A port
    will be assigned to the user and the user's donation keys will be set.
  <Returns>
    GeniUser instance (our GeniUser model, not the django User) corresponding to the
    newly registered user.
  """
  # If the frontend code that called this function wants to know which field
  # is invalid, it must call the validation functions itself before making the
  # call to register_user().
  # These will raise a ValidationError if any of the fields are invalid.
  # These ensure that the data is of the correct type (e.g. a string) as well as
  # that we like the content of the variable.
  validations.validate_username(username)
  validations.validate_password(password)
  validations.validate_username_and_password_different(username, password)
  validations.validate_email(email)
  validations.validate_affiliation(affiliation)
  if pubkey is not None:
    validations.validate_pubkey_string(pubkey)
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, username)
  try:
    # Ensure there is not already a user with this username.
    try:
      # Raises a DoesNotExistError if the user doesn't exist.
      maindb.get_user(username)
      raise UsernameAlreadyExistsError
    except DoesNotExistError:
      # This is what we wanted: the username isn't already taken.
      pass
    
    # Get a key pair from the keygen api if the user didn't supply their own pubkey.
    if pubkey is None:
      (pubkey, privkey) = keygen.generate_keypair()
    else:
      privkey = None
    
    # Generate a donor key for this user. This is done through the backend
    # as the private key must be stored in the keydb, which the website cannot
    # directly access.
    keydescription = "donor:" + username
    donor_pubkey = backend.generate_key(keydescription)
    
    # Create the user record.
    geniuser = maindb.create_user(username, password, email, affiliation, pubkey, privkey, donor_pubkey)
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, username)
    lockserver.destroy_lockserver_handle(lockserver_handle)
    
  return geniuser
  



#def change_user_pubkey(geniuser, user_pubkey):
#  """
#  <Purpose>
#    Assigns a new key pair to this user.
#  <Arguments>
#    geniuser
#    user_pubkey
#  <Exceptions>
#    ProgrammerError
#      If the user is not a valid GeniUser object or if user_pubkey is not a
#      valid pubkey.
#  <Side Effects>
#    The user's public key is replaced with the provided one. If they had a
#    private key still stored in our database, that private key is deleted.
#  <Returns>
#    None
#  """
#  raise NotImplementedError




# JTC: Added for installers.
@log_function_call
def get_user_for_installers(username):
  """
  <Purpose>
    Gets the user record corresponding to the given username.
    IMPORTANT: Used ONLY FOR getting the user object for downloading/building installers.
               Do NOT use for any other purpose, as this function does not validate passwords.
  <Arguments>
    username
      The username (must be a string).
  <Exceptions>
    DoesNotExistError
      If there is no user with the specified username and password.
  <Side Effects>
    None
  <Returns>
    The GeniUser instance if the username is valid.
  """
  assert_str(username)
  
  return maindb.get_user(username)





@log_function_call
def get_user_without_password(username):
  """
  <Purpose>
    Gets the user record corresponding to the given username.
  <Arguments>
    username
      The username (must be a string).
  <Exceptions>
    DoesNotExistError
      If there is no user with the specified username.
  <Side Effects>
    None
  <Returns>
    The GeniUser instance if the username is valid.
  """
  assert_str(username)
  
  return maindb.get_user(username)





@log_function_call_and_only_first_argument
def get_user_with_password(username, password):
  """
  <Purpose>
    Gets the user record corresponding to the username and password.
  <Arguments>
    username
      The username (must be a string).
    password
      The password (must be a string).
  <Exceptions>
    DoesNotExistError
      If there is no user with the specified username and password.
  <Side Effects>
    None
  <Returns>
    The GeniUser instance if the username/password are valid.
  """
  assert_str(username)
  assert_str(password)
  
  return maindb.get_user_with_password(username, password)





@log_function_call_and_only_first_argument
def get_user_with_api_key(username, api_key):
  """
  <Purpose>
    Gets the user record corresponding to the username and api_key.
  <Arguments>
    username
      The username (must be a string).
    api_key
      The api_key (must be a string).
  <Exceptions>
    DoesNotExistError
      If there is no user with the specified username and api_key.
  <Side Effects>
    None
  <Returns>
    The GeniUser instance if the username/api_key are valid.
  """
  assert_str(username)
  assert_str(api_key)
  
  return maindb.get_user_with_api_key(username, api_key)  

  



# Not logging arguments. The call to get_user_with_password()
# made within this function will log those details.
@log_function_call_without_arguments
def login_user(request, username, password):
  """
  <Purpose>
    Log a user in to a session if the username and password are valid. This
    allows future requests that are part ofsame session to obtain the user
    object through calls to get_logged_in_user(). This function should not
    be used through the xmlrpc frontend as there is no concept of the session
    there.
  <Arguments>
    request
      The HttpRequest object of the user's request through the frontend.
    username
      The username of the user to be logged in.
    password
      The password of the user to be logged in.
  <Exceptions>
    DoesNotExistError
      If there is no user with the provided username and password.
  <Side Effects>
    Associates the user with a session corresponding to the request.
  <Returns>
    None
  """
  assert_str(username)
  assert_str(password)
  
  # Raises a DoesNotExistError if there is no such user. We could actually
  # skip this and only rely on authenticate, but I'd like to make sure that
  # the get_user_with_password function gets called before letting the user
  # access the site. The the note further down about checking the is_active
  # field for one example of why.
  get_user_with_password(username, password)
  
  # The auth.authenticate() method must be called before the auth.login()
  # method, as this method sets some values in the user object that are
  # required by auth.login().
  djangouser = django.contrib.auth.authenticate(username=username, password=password)
  
  # Note that we aren't checking the is_active field which is part of the base
  # django user class. If we want to be able to disable user accounts, we need
  # to be sure to do it in a way that will work for all frontends, including
  # xmlrpc. So, for example, the get_user_with_* methods could be changed.
  # If we looked for it only here, then the user could still perform actions
  # via xmlrpc.
  
  # Logs the user in via django's auth platform. This associates the user
  # with the current session. 
  django.contrib.auth.login(request, djangouser)
  




@log_function_call
def get_logged_in_user(request):
  """
  <Purpose>
    Determine the user logged in to the current session.
    This function should not be used through the xmlrpc frontend as there is
    no concept of the session there.
  <Arguments>
    request
      The HttpRequest object of the user's request through the frontend.
  <Exceptions>
    DoesNotExistError
      If there is no user logged in to the current session.
  <Side Effects>
    None
  <Returns>
    The GeniUser object of the logged in user.
  """
  # See http://docs.djangoproject.com/en/dev/topics/auth/#authentication-in-web-requests
  # for an explanation of request.user.is_authenticated().
  if request.user.is_authenticated():
    return maindb.get_user(request.user.username)
  else:
    raise DoesNotExistError





@log_function_call
def logout_user(request):
  """
  <Purpose>
    Logs out the user logged in to the current session, if any.
  <Arguments>
    request
      The HttpRequest object of the user's request through the frontend.
  <Exceptions>
    None
  <Side Effects>
    Any user logged in to the current session is no longer logged in.
  <Returns>
    None
  """
  request.session.flush()





@log_function_call
def change_user_keys(geniuser, pubkey=None):
  """
  <Purpose>
    Sets a new public/private key for the user and initiates the change
    of user keys on all vessels the user has access to. If pubkey is
    provided, that is used as the user's new pubkey. If pubkey is not
    provided, a new public/private keypair is generated for the user.
  <Arguments>
    geniuser
      A GeniUser object of the user whose keys are to be updated.
  <Exceptions>
    ValidationError
      If the pubkey is provided and is invalid.
  <Side Effects>
    The public and private keys of the user are replaced in the database with
    new keys (if pubkey was provided, the private key in the database will
    be empty, otherwise it will be the generated private key). All vessels the
    user has access to are marked as needing to have their user keys sync'd.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  if pubkey is not None:
    validations.validate_pubkey_string(pubkey)
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    # Get a key pair from the keygen api if the user didn't supply their own pubkey.
    if pubkey is None:
      (pubkey, privkey) = keygen.generate_keypair()
    else:
      privkey = None    
    
    maindb.set_user_keys(geniuser, pubkey, privkey)
    
    # Now we need to find all of the vessels the user has access to and set
    # them to have their user keys updated by the backend.
    vessel_list = maindb.get_vessels_accessible_by_user(geniuser)
    if vessel_list:
      vessels.flag_vessels_for_user_keys_sync(lockserver_handle, vessel_list)
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)




	
def get_useable_ports():
  """
  <Purpose>
     Gets the allowed user port range
  <Arguments>
	None
  <Exceptions>
   None
  <Side Effects>
    None
  <Returns>
    The allowed user port range which is globally defined in maindb.
  """
  return maindb.get_allowed_user_ports()





@log_function_call
def change_user_email(geniuser, new_email):
  """
  <Purpose>
     Sets a new email for the user 
  <Arguments>
    geniuser
      A GeniUser object of the user whose email is to be updated.
    new_email
      the new email value
  <Exceptions>
    ValidationError
      If the email is provided and is invalid.
  <Side Effects>
    The geniuser email gets changed to the new value(in the db).
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  #validate its a real email.  The frontend should already
  #checks for this but we validate again just in case.
  validations.validate_email(new_email)
 
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())

    maindb.set_user_email(geniuser, new_email)
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call
def change_user_affiliation(geniuser, new_affiliation):
  """
  <Purpose>
     Sets a new affiliation for the user 
  <Arguments>
    geniuser
      A GeniUser object of the user whose affiliation is to be updated.
    new_affiliation
      the new affiliation value
  <Exceptions>
    ValidationError
      If the affiliation is provided and is invalid.
  <Side Effects>
    The geniuser affiliation gets changed to the new value(in the db).
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  #Determines if the new affiliation is valid.  The frontend should already
  #checks for this but we validate again here just in case.
  validations.validate_affiliation(new_affiliation)
 
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())

    maindb.set_user_affiliation(geniuser, new_affiliation)
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call
def change_user_port(geniuser, new_port):
  """
  <Purpose>
     Sets a new port for the user 
  <Arguments>
    geniuser
      A GeniUser object of the user whose port is to be changed.
    new_port
      the new port value
  <Exceptions>
    ValidationError
      If the port is provided and it is not in the allowed range.
  <Side Effects>
    the geniuser port gets changed to the new value(in the db).
  <Returns>
    None
  """
  assert_geniuser(geniuser)

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())

    maindb.set_user_port(geniuser, new_port)
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)




	
@log_function_call_and_only_first_argument
def change_user_password(geniuser, new_password):
  """
  <Purpose>
     Sets a new password for the geniuser. 
  <Arguments>
    geniuser
      A GeniUser object of the user whose password is to be changed.
    new_password
      the user specificed new password value.
  <Exceptions>
    ValidationError
      If the password is provided and is invalid.
  <Side Effects>
    The geniuser password gets changed to the new value (in the db).
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  #Determines if the new password is strong enough.  The frontend should already
  #check for this but we validate again here just in case.
  validations.validate_password(new_password)
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())

    maindb.set_user_password(geniuser, new_password)
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call
def regenerate_api_key(geniuser):
  """
  <Purpose>
    Regenerates the user's API key.
  <Arguments>
    geniuser
      A GeniUser object of the user whose api key is to be regenerated.
  <Exceptions>
    None
  <Side Effects>
    The API key for the user is updated in the database.
  <Returns>
    The new API key.
  """
  assert_geniuser(geniuser)
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect changes we make to the object.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    return maindb.regenerate_api_key(geniuser)
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle) 



  

@log_function_call
def delete_private_key(geniuser):
  """
  <Purpose>
    Deletes the private key of the specified user.
  <Arguments>
    geniuser
      A GeniUser object of the user whose private key is to be deleted.
  <Exceptions>
    None
  <Side Effects>
    The private key belonging to the user is deleted if it exists, otherwise
    the user account is not modified.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    # We don't use the user object we retrieve because we want the
    # object passed in to the function to reflect the deletion of the key.
    # That is, we want the object passed in to have the user_privkey be None
    # when this function returns.
    try:
      maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    maindb.delete_user_private_key(geniuser)
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call_without_return
def get_private_key(geniuser):
  """
  <Purpose>
    Gets the private key of the specified user.
  <Arguments>
    geniuser
      A GeniUser object of the user whose private key is to be retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The string containing the user's private key or None if the user's private
    key is not stored by us (e.g. that is, either we never had it or the user
    deleted it).
  """
  assert_geniuser(geniuser)
  
  return geniuser.user_privkey





@log_function_call
def get_donations(geniuser):
  """
  <Purpose>
    Gets a list of donations made by a specific user.
  <Arguments>
    geniuser
      The GeniUser object who is the donor of the donations.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of the donations made by geniuser.
  """
  assert_geniuser(geniuser)
  
  # This is read-only, so not locking the user.
  return maindb.get_donations_by_user(geniuser)





@log_function_call
def get_acquired_vessels(geniuser):
  """
  <Purpose>
    Gets a list of vessels that have been acquired by the user.
  <Arguments>
    user
      A GeniUser object of the user who is assigned to the vessels.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects for the vessels that have been acquired by the
    user.
  """
  assert_geniuser(geniuser)
  
  # This is read-only, so not locking the user.
  return maindb.get_acquired_vessels(geniuser)





# @log_action is a decorator that records details of vessel-affecting
# operations in the database. This decorator should be kept in mind whenever
# the arguments or return value to this function are changed.
@log_action
@log_function_call
def acquire_vessels(geniuser, vesselcount, vesseltype):
  """
  <Purpose>
    Acquire unused vessels of a given type for a user. For information on how
    the specified vesseltype affects which vessels will be considered
    to satisfy the request, see the type-specific functions that are called
    by this function.
  <Arguments>
    geniuser
      The GeniUser which will be assigned the vessels.
    vesselcount
      The number of vessels to acquire (a positive integer).
    vesseltype
      The type of vessels to acquire. One of either 'lan', 'wan', 'nat', or 'rand'.
  <Exceptions>
    UnableToAcquireResourcesError
      If not able to acquire the requested vessels (in this case, no vessels
      will be acquired).
    InsufficientUserResourcesError
      The user does not have enough vessel credits to acquire the number of
      vessels requested.
  <Side Effects>
    A total of 'vesselcount' previously-unassigned vessels of the specified
    vesseltype have been acquired by the user.
  <Returns>
    A list of the vessels as a result of this function call.
  """
  assert_geniuser(geniuser)
  assert_positive_int(vesselcount)
  assert_str(vesseltype)

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    try:
      geniuser = maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    # Ensure the user is allowed to acquire these resources. This call will
    # raise an InsufficientUserResourcesError if the additional vessels would
    # cause the user to be over their limit.
    maindb.require_user_can_acquire_resources(geniuser, vesselcount)
    
    if vesseltype == 'wan':
      acquired_list = vessels.acquire_wan_vessels(lockserver_handle, geniuser, vesselcount)
    elif vesseltype == 'lan':
      acquired_list = vessels.acquire_lan_vessels(lockserver_handle, geniuser, vesselcount)
    elif vesseltype == 'nat':
      acquired_list = vessels.acquire_nat_vessels(lockserver_handle, geniuser, vesselcount)
    elif vesseltype == 'rand':
      acquired_list = vessels.acquire_rand_vessels(lockserver_handle, geniuser, vesselcount)
    else:
      raise ProgrammerError("Vessel type '%s' is not a valid type" % vesseltype)
    
    return acquired_list
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





# @log_action is a decorator that records details of vessel-affecting
# operations in the database. This decorator should be kept in mind whenever
# the arguments or return value to this function are changed.
@log_action
@log_function_call
def acquire_specific_vessels(geniuser, vessel_list):
  """
  <Purpose>
    Attempt to acquire specific vessels for a user.
  <Arguments>
    geniuser
      The GeniUser which will be assigned the vessels.
    vessel_list
      A list of vessels to be acquired for the user.
  <Exceptions>
    InsufficientUserResourcesError
      The user does not have enough vessel credits to acquire the number of
      vessels requested.
    InvalidRequestError
      If the list of vessels is empty.
  <Side Effects>
    Zero or more of the vessels in vessel_list have been acquired by the user.
  <Returns>
    A list of the vessels acquired as a result of this function call. The
    length of this list may be less than the length of vessel_list if one or
    more of the vessels in vessel_list could not be acquired.
  """
  assert_geniuser(geniuser)
  assert_list(vessel_list)
  for vessel in vessel_list:
    assert_vessel(vessel)

  if not vessel_list:
    raise InvalidRequestError("The list of vessels cannot be empty.")

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    try:
      geniuser = maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    # Ensure the user is allowed to acquire these resources. This call will
    # raise an InsufficientUserResourcesError if the additional vessels would
    # cause the user to be over their limit.
    maindb.require_user_can_acquire_resources(geniuser, len(vessel_list))
    
    return vessels.acquire_specific_vessels_best_effort(lockserver_handle, geniuser, vessel_list)
    
  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





# @log_action is a decorator that records details of vessel-affecting
# operations in the database. This decorator should be kept in mind whenever
# the arguments or return value to this function are changed.
@log_action
@log_function_call
def release_vessels(geniuser, vessel_list):
  """
  <Purpose>
    Remove a user from a vessel that is assigned to the user.
  <Arguments>
    geniuser
      The GeniUser who is to be removed from the vessel.
    vessel_list
      A list of vessels the user is to be removed from.
  <Exceptions>
    InvalidRequestError
      If any of the vessels in the vessel_list are not currently acquired by
      geniuser or if the list of vessels is empty.
  <Side Effects>
    The vessel is no longer assigned to the user. If this was the last user
    assigned to the vessel, the vessel is freed.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  assert_list(vessel_list)
  for vessel in vessel_list:
    assert_vessel(vessel)

  if not vessel_list:
    raise InvalidRequestError("The list of vessels cannot be empty.")

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    try:
      geniuser = maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    vessels.release_vessels(lockserver_handle, geniuser, vessel_list)

  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call
def release_all_vessels(geniuser):
  """
  <Purpose>
    Release all vessels that have been acquired by the user.
  <Arguments>
    geniuser
      The GeniUser who is to have their vessels released.
  <Exceptions>
    None
  <Side Effects>
    All of the user's acquired vessels at the time of this function call
    have been released. This function does not guarantee that the user has
    no acquired vessels at the time that it returns, though.
  <Returns>
    None
  """
  # We get the list of vessels without holding a lock. An acquisition
  # request or other request could sneak in after we get the vessel list but
  # before we hold the lock. I'm not going to worry about this because it won't
  # lead to data integrity. At worst the user could get an error about not
  # being able to release all vessels.

  # Get a list of all vessels acquired by the user.
  vessel_list = maindb.get_acquired_vessels(geniuser)
  
  if not vessel_list:
    raise InvalidRequestError("You have no vessels and so nothing to release.")
  
  release_vessels(geniuser, vessel_list)
  




# @log_action is a decorator that records details of vessel-affecting
# operations in the database. This decorator should be kept in mind whenever
# the arguments or return value to this function are changed.
@log_action
@log_function_call
def renew_vessels(geniuser, vessel_list):
  """
  <Purpose>
    Extend the expiration dates of vessels acquired by a user.
  <Arguments>
    geniuser
      The GeniUser whose vessels are to be renewed.
    vessel_list
      A list of vessels to be renewed.
  <Exceptions>
    InvalidRequestError
      If any of the vessels in the vessel_list are not currently acquired by
      geniuser or if the list of vessels is empty.
    InsufficientUserResourcesError
      If the user is currently over their limit of acquired resources.
  <Side Effects>
    The vessels are renewed to the maximum time vessels can be acquired for,
    regardless of their previous individual expiration times.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  assert_list(vessel_list)
  for vessel in vessel_list:
    assert_vessel(vessel)

  if not vessel_list:
    raise InvalidRequestError("The list of vessels cannot be empty.")

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)
  
  try:
    # Make sure the user still exists now that we hold the lock. Also makes
    # sure that we see any changes made to the user before we obtained the lock.
    try:
      geniuser = maindb.get_user(geniuser.username)
    except DoesNotExistError:
      raise InternalError(traceback.format_exc())
    
    # Ensure the user is not over their limit of acquired vessels due to
    # donations of theirs having gone offline. This call will raise an
    # InsufficientUserResourcesError if the user is currently over their
    # limit.
    vesselcount = 0
    maindb.require_user_can_acquire_resources(geniuser, vesselcount)
    
    # The vessels.renew_vessels function is responsible for ensuring that the
    # vessels belong to this user. We let the other function do the check
    # because we want to hold locks on the vessels' nodes before checking.
    vessels.renew_vessels(lockserver_handle, geniuser, vessel_list)

  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)





@log_function_call
def renew_all_vessels(geniuser):
  """
  <Purpose>
    Extend the expiration dates of vessels acquired by a user.
  <Arguments>
    geniuser
      The GeniUser whose vessels are to be renewed.
  <Exceptions>
    InvalidRequestError
      If the user has no acquired vessels.
    InsufficientUserResourcesError
      If the user is currently over their limit of acquired resources.
  <Side Effects>
    All vessels acquired by the user at the time of this function all are
    renewed to the maximum time vessels can be acquired for, regardless of
    their previous individual expiration times.
  <Returns>
    None
  """
  # We get the list of vessels without holding a lock. An acquisition
  # request or other request could sneak in after we get the vessel list but
  # before we hold the lock. I'm not going to worry about this because it won't
  # lead to data integrity. At worst the user could get an error about not
  # being able to renew all vessels.
    
  # Get a list of all vessels acquired by the user.
  vessel_list = maindb.get_acquired_vessels(geniuser)
  
  if not vessel_list:
    raise InvalidRequestError("You have no vessels and so nothing to renew.")
  
  renew_vessels(geniuser, vessel_list)





# Not logging the function call for now.
def get_vessel_list(vesselhandle_list):
  """
  <Purpose>
    Convert a list of vesselhandles into a list of Vessel objects.
  <Arguments>
    vesselhandle_list
      A list of strings where each string is a vesselhandle of the format
      "nodeid:vesselname"
  <Exceptions>
    DoesNotExistError
      If a specified vessel does not exist.
    InvalidRequestError
      If any vesselhandle in the list is not in the correct format.
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects.
  """
  assert_list_of_str(vesselhandle_list)
  
  vessel_list = []
  
  for vesselhandle in vesselhandle_list:
    if len((vesselhandle.split(":"))) != 2:
      raise InvalidRequestError("Invalid vesselhandle: " + vesselhandle)
    
    (nodeid, vesselname) = vesselhandle.split(":")
    # Raises DoesNotExistError if there is no such node/vessel.
    vessel = maindb.get_vessel(nodeid, vesselname)
    vessel_list.append(vessel)
    
  return vessel_list


  


# Not logging the function call for now.
def get_vessel_infodict_list(vessel_list):
  """
  <Purpose>
    Convert a list of Vessel objects into a list of vessel infodicts.
    An "infodict" is a dictionary of vessel information that contains data
    which is safe for public display.
    
    This function needs to return lists of dictionaries with a minimum of the
    following, according to https://seattle.cs.washington.edu/wiki/SeattleGeniAPI:
      {'node_ip':node_ip, 'node_port':node_port, 'vessel_id':vessel_id, 
      'node_id':node_id, 'handle':handle}
  <Arguments>
    vessel_list
      A list of Vessel objects.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of vessel infodicts.
  """
  infodict_list = []
  
  for vessel in vessel_list:
    vessel_info = {}
    
    vessel_info["node_id"] = maindb.get_node_identifier_from_vessel(vessel)
    node = maindb.get_node(vessel_info["node_id"])
    
    vessel_info["node_ip"] = node.last_known_ip
    vessel_info["node_port"] = node.last_known_port
    vessel_info["vessel_id"] = vessel.name
    
    vessel_info["handle"] = vessel_info["node_id"] + ":" + vessel.name
    
    vessel_info["is_active"] = node.is_active
    
    expires_in_timedelta = vessel.date_expires - datetime.datetime.now()
    # The timedelta object stores information in two parts: days and seconds.
    vessel_info["expires_in_seconds"] = (expires_in_timedelta.days * 3600 * 24) + expires_in_timedelta.seconds
      
    infodict_list.append(vessel_info)
    
  return infodict_list





def get_total_vessel_credits(geniuser):
  """
  <Purpose>
    Determine the total number of vessels the user is allowed to acquire,
    regardless of how many they have already acquired.
  <Arguments>
    geniuser
      The GeniUser whose total vessel credit count is wanted.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The total number of vessels the user is allowed to acquire, regardless
    of how many they currently have acquired.
  """
  assert_geniuser(geniuser)
  
  return maindb.get_user_total_vessel_credits(geniuser)


def get_free_vessel_credits_amount(geniuser):
  """
  <Purpose>
    Determine the total number of free vessel credits the user is given.
  <Arguments>
    geniuser
      The GeniUser whose free vessel credits is wanted
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The total number of vessels the user is given for free.
  """
  assert_geniuser(geniuser)

  return maindb.get_user_free_vessel_credits(geniuser)


def get_available_vessel_credits(geniuser):
  """
  <Purpose>
    Determine the number vessels the user is allowed to acquire at the moment
    (that is, the total vessel credits they have minus the number of vessels
    they have acquired).
  <Arguments>
    geniuser
      The GeniUser whose available vessel credit count is wanted.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The maximum number of vessels the user is allowed to acquire at this
    moment without exceeding the total number they are allowed to acquire.
  """
  assert_geniuser(geniuser)
  
  max_allowed_vessels = maindb.get_user_total_vessel_credits(geniuser)
  acquired_vessel_count = len(maindb.get_acquired_vessels(geniuser))
  
  if acquired_vessel_count >= max_allowed_vessels:
    return 0
  else:
    return max_allowed_vessels - acquired_vessel_count
