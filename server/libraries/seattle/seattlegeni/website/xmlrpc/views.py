"""
<Program>
  views.py

<Started>
  6 July 2009

<Author>
  Jason Chen
  Justin Samuel

<Purpose>
  This file defines all of the public SeattleGeni XMLRPC functions. When the
  SeattleGENI XMLRPC API changes, this file will generally always need to be
  modified.  

  To create a new xmlrpc function, just create a new method in the
  PublicXMLRPCFunctions class below. All public methods in that class
  are automatically registered with the xmlrpc dispatcher.

  The functions defined here should generally be making calls to the
  controller interface to perform any work or retrieve data.

  Be sure to use the following decorators with each function, in this order:

  @staticmethod -- this is a python decorator that prevents 'self'
                   from being passed as the first argument.
  @log_function_call -- this is our own decorator for logging purposes.
"""

# To send the admins emails when there's an unhandled exception.
import django.core.mail 

import random
import string
import traceback

# Used for raising xmlrpc faults
import xmlrpclib

from seattlegeni.website import settings

# Make available all of our own standard exceptions.
from seattlegeni.common.exceptions import *

from seattlegeni.common.util import assertions
from seattlegeni.common.util import log

# This is the logging decorator we use.
from seattlegeni.common.util.decorators import log_function_call
from seattlegeni.common.util.decorators import log_function_call_without_first_argument

# All of the work that needs to be done is passed through the controller interface.
from seattlegeni.website.control import interface

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")





# The number of bytes of random padding data, not including the "!" separator,
# which is included in the encrypted API key.
# Don't change this without changing the API spec and the xmlrpc client.
ENCRYPTED_API_KEY_PADDING_BYTES = 20



# XMLRPC Fault Code Constants
FAULTCODE_INTERNALERROR = 100
FAULTCODE_AUTHERROR = 101
FAULTCODE_INVALIDREQUEST = 102
FAULTCODE_NOTENOUGHCREDITS = 103
# 104 used to be used for "private key doesn't exist".
FAULTCODE_UNABLETOACQUIRE = 105




class PublicXMLRPCFunctions(object):
  """
  All public functions of this class are automatically exposed as part of the
  xmlrpc interface.
  
  Each method should be sure to check the user input and return useful errors
  to the client if the input is invalid. Note that raising an AssertionError
  (e.g. through a call to an assert_* method) won't be sufficient, as those
  should only indicate something going wrong in our code. 
  """

  def _dispatch(self, method, args):
    """
    We provide a _dispatch function (which SimpleXMLRPCServer looks for and
    uses) so that we can log exceptions due to our programming errors within
    seattlegeni as well to detect incorrect usage by clients.
    """
      
    try:
      # Get the requested function (making sure it exists).
      try:
        func = getattr(self, method)
      except AttributeError:
        raise InvalidRequestError("The requested method '" + method + "' doesn't exist.")
      
      # Call the requested function.
      return func(*args)
    
    except InvalidRequestError:
      log.error("The xmlrpc server was used incorrectly: " + traceback.format_exc())
      raise
    
    except xmlrpclib.Fault:
      # A xmlrpc Fault was intentionally raised by the code in this module.
      raise
    
    except Exception, e:
      # We assume all other exceptions are bugs in our code.

      # We use the log message as the basis for the email message, as well.
      logmessage = "Internal error while handling an xmlrpc request: " + traceback.format_exc()
      log.critical(logmessage)

      # Normally django will send an email to the ADMINS defined in settings.py
      # when an exception occurs. However, our xmlrpc dispatcher will turn this
      # into a Fault that is returned to the client. So, django won't see it as
      # an uncaught exception. Therefore, we have to send it ourselves.
      if not settings.DEBUG:
        subject = "Error handling xmlrpc request '" + method + "': " + str(type(e)) + " " + str(e)
        
        emailmessage = logmessage + "\n\n"
        emailmessage += "XMLRPC method called: " + method + "\n"
        
        # If the first argument looks like auth info, don't include the
        # api_key in the email we send. Otherwise, include all the args.
        # We wrap this in a try block just in case we screw this up we want to
        # be sure we get an email still.
        try:
          if len(args) > 0 and isinstance(args[0], dict) and "username" in args[0]:
            emailmessage += "Username: " + str(args[0]["username"]) + "\n"
            if len(args) > 1:
              emailmessage += "Non-auth arguments: " + str(args[1:]) + "\n"
            else:
              emailmessage += "There were no non-auth arguments." + "\n"
          else:
            emailmessage += "Arguments: " + str(args) + "\n"
        except:
          pass
          
        # Send an email to the addresses listed in settings.ADMINS
        django.core.mail.mail_admins(subject, emailmessage)
      
      # It's not unlikely that the user ends up seeing this message, so we
      # are careful about what the content of the message is. We don't
      # include the exception trace.
      raise xmlrpclib.Fault(FAULTCODE_INTERNALERROR, "Internal error while handling the xmlrpc request.")
      


  @staticmethod
  @log_function_call
  def acquire_resources(auth, rspec):
    """
    <Purpose>
      Acquires resources for users over XMLRPC. 
    <Arguments>
      auth
        An authorization dict.
      rspec
        A resource specification dict of the form {'rspec_type':type, 'number_of_nodes':num}
    <Exceptions>
      Raises xmlrpclib Fault objects:
        FAULTCODE_INTERNALERROR for internal errors.
        FAULTCODE_INVALIDREQUEST for bad user input.
        FAULTCODE_NOTENOUGHCREDITS if user has insufficient vessel credits to complete request.
    <Returns>
      A list of 'info' dictionaries, each 'infodict' contains acquired vessel info.
    """
    geni_user = _auth(auth)
    
    if not isinstance(rspec, dict):
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "rspec is an invalid data type.")
    
    try:
      resource_type = rspec['rspec_type']
    except KeyError:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "rspec is missing rspec_type")
    
    try:
      num_vessels = rspec['number_of_nodes']
    except KeyError:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "rspec is missing number_of_nodes")
    
    acquired_vessels = []
    
    # validate rspec data
    if not isinstance(resource_type, str) or not isinstance(num_vessels, int):
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "rspec has invalid data types.")
    
    if resource_type not in ['wan', 'lan', 'nat', 'random'] or num_vessels < 1:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "rspec has invalid values.")
      
    # The interface.acquire_vessels() call expects 'rand' instead of 'random'.
    if resource_type == 'random':
      resource_type = 'rand'
    
    try:
      acquired_vessels = interface.acquire_vessels(geni_user, num_vessels, resource_type)
    except UnableToAcquireResourcesError, err:
      raise xmlrpclib.Fault(FAULTCODE_UNABLETOACQUIRE, "Unable to fulfill vessel acquire request at this given time. Details: " + str(err))
    except InsufficientUserResourcesError, err:
      raise xmlrpclib.Fault(FAULTCODE_NOTENOUGHCREDITS, "You do not have enough vessel credits to acquire the number of vessels requested.")
    
    # since acquire_vessels returns a list of Vessel objects, we
    # need to convert them into a list of 'info' dictionaries.
    return interface.get_vessel_infodict_list(acquired_vessels)



  @staticmethod
  @log_function_call
  def acquire_specific_vessels(auth, vesselhandle_list):
    """
    <Purpose>
      Acquires specific vessels for a user. This will be best effort. Zero or
      more of the vessels may be acquired. The list, however, cannot include
      more vessels than the maximum number the user is allowed to acquire.
    <Arguments>
      auth
        An authorization dict.
      vesselhandle_list
        A list of vessel handles.
    <Exceptions>
      Raises xmlrpclib Fault objects:
        FAULTCODE_INTERNALERROR for internal errors.
        FAULTCODE_INVALIDREQUEST for bad user input.
        FAULTCODE_NOTENOUGHCREDITS if user has insufficient vessel credits to complete request.
    <Returns>
      A list of 'info' dictionaries, each 'infodict' contains acquired vessel info.
    """
    geni_user = _auth(auth)
    
    if not isinstance(vesselhandle_list, list):
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Invalid data type for handle list.")
    
    # Remove duplicates to avoid race condition where the database is
    # updated simultaneously for the same vessel, raising a duplicate
    # key error.
    vesselhandle_list = list(set(vesselhandle_list))

    # since we're given a list of vessel 'handles', we need to convert them to a 
    # list of actual Vessel objects; as release_vessels_of_user expects Vessel objs.
    try:
      list_of_vessel_objs = interface.get_vessel_list(vesselhandle_list)
    except DoesNotExistError, err:
      # given handle refers to a non-existant vessel
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    except InvalidRequestError, err:
      # A handle is of an invalid format or the list of vessels is empty.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    
    try:
      acquired_vessels = interface.acquire_specific_vessels(geni_user, list_of_vessel_objs)
    except InvalidRequestError, err:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    except InsufficientUserResourcesError, err:
      raise xmlrpclib.Fault(FAULTCODE_NOTENOUGHCREDITS, "You do not have enough " + 
                            "vessel credits to acquire the number of vessels requested.")
    
    # Convert the list of vessel objects into a list of 'info' dictionaries.
    return interface.get_vessel_infodict_list(acquired_vessels)



  @staticmethod
  @log_function_call
  def release_resources(auth, vesselhandle_list):
    """
    <Purpose>
      Release resources for a user over XMLRPC.
    <Arguments>
      auth
        An authorization dict.
      vesselhandle_list
        A list of vessel handles
    <Exceptions>
      Raises xmlrpclib Fault objects:
        FAULTCODE_INVALIDREQUEST if a user provides invalid vessel handles.
    <Returns>
      0 on success. Raises a fault otherwise.
    """
    geni_user = _auth(auth)
  
    if not isinstance(vesselhandle_list, list):
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Invalid data type for handle list.")
    
    # since we're given a list of vessel 'handles', we need to convert them to a 
    # list of actual Vessel objects; as release_vessels_of_user expects Vessel objs.
    try:
      list_of_vessel_objs = interface.get_vessel_list(vesselhandle_list)
    except DoesNotExistError, err:
      # given handle refers to a non-existant vessel
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    except InvalidRequestError, err:
      # A handle is of an invalid format or the list of vessels is empty.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    
    try:
      interface.release_vessels(geni_user, list_of_vessel_objs)
    except InvalidRequestError, err:
      # vessel exists but isn't valid for you to use.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    
    return 0



  @staticmethod
  @log_function_call
  def renew_resources(auth, vesselhandle_list):
    """
    <Purpose>
      Renew resources for a user over XMLRPC. Renewal changes the expiration
      time to the maximum allowed.
    <Arguments>
      auth
        An authorization dict.
      vesselhandle_list
        A list of vessel handles
    <Exceptions>
      Raises xmlrpclib Fault objects with fault codes:
        FAULTCODE_INVALIDREQUEST if a user provides invalid vessel handles.
        FAULTCODE_NOTENOUGHCREDITS if user has insufficient vessel credits to complete request.
    <Returns>
      0 on success. Raises a fault otherwise.
    """
    geni_user = _auth(auth)
  
    if not isinstance(vesselhandle_list, list):
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Invalid data type for handle list.")
    
    for handle in vesselhandle_list:
      if not isinstance(handle, str):
        raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, 
                              "Invalid data type for handle. Expected str, received " + str(type(handle)))

    # since we're given a list of vessel 'handles', we need to convert them to a 
    # list of actual Vessel objects.
    try:
      list_of_vessel_objs = interface.get_vessel_list(vesselhandle_list)
    except DoesNotExistError, err:
      # The handle refers to a non-existent vessel.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    except InvalidRequestError, err:
      # A handle is of an invalid format or the list of vessels is empty.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    
    try:
      interface.renew_vessels(geni_user, list_of_vessel_objs)
    except InvalidRequestError, err:
      # The vessel exists but isn't valid for this user to use.
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, str(err))
    except InsufficientUserResourcesError, err:
      message = "Vessels cannot be renewed because you are currently"
      message += " over your vessel credit limit: "
      message += str(err)
      raise xmlrpclib.Fault(FAULTCODE_NOTENOUGHCREDITS, message)
    
    return 0

  
  
  @staticmethod
  @log_function_call
  def get_resource_info(auth):
    """
    <Purpose>
      Gets a user's acquired vessels over XMLRPC.
    <Arguments>
      auth
        An authorization dict.
    <Exceptions>
      None.
    <Returns>
      A list of 'info' dictionaries, each 'infodict' contains vessel info.
    """
    geni_user = _auth(auth)
    user_vessels = interface.get_acquired_vessels(geni_user)
    return interface.get_vessel_infodict_list(user_vessels)
  
  
  
  @staticmethod
  @log_function_call
  def get_account_info(auth):
    """
    <Purpose>
      Gets a user's account info for a client over XMLRPC.
    <Arguments>
      auth
        An authorization dict.
    <Exceptions>
      None.
    <Returns>
      A dictionary containing account info.
    """
    geni_user = _auth(auth)
    user_port = geni_user.usable_vessel_port
    user_name = geni_user.username
    max_vessels = interface.get_total_vessel_credits(geni_user)
    user_affiliation = geni_user.affiliation
    infodict = {'user_port':user_port, 'user_name':user_name,
                'max_vessels':max_vessels, 'user_affiliation':user_affiliation}
    return infodict
  
  
  
  @staticmethod
  @log_function_call
  def get_public_key(auth):
    # Gets a user's public key.
    geni_user = _auth(auth)
    return geni_user.user_pubkey



  @staticmethod
  @log_function_call
  def get_encrypted_api_key(username):
    """
    <Purpose>
      Retrieve the account's API key encrypted with the account's public key.
      This provides the holder of an account's private key a means of obtaining
      the SeattleGENI API key for the account. A side effect is that this also
      provide a means of determining whether an account exists on seattlegeni.
      However, we do not protect against such querying here because the same
      can be determined in a handful of other ways through the html interface.
      
      This approach of obtaining the encrypted api key can be removed later if
      we implement a way to sign requests.
    <Arguments>
      username
        The username of the account whose encrypted API key we want.
    <Exceptions>
      Raises xmlrpclib Fault objects with fault codes:
        FAULTCODE_INVALIDREQUEST if a the provided username is not a string
          specifying a valid (existing) account username.
    <Returns>
      An string that represents DATA encrypted by (seattlelib) rsa.repy's
      rsa_encrypt() function. DATA is a string that is the concatenation of
      a random string of 0-9a-fA-F of fixed length, an exclamation mark, and
      the API key.
      
      For example, DATA may be the following string:
        l28yDKLQGqhqdfDquDq0433!AD98OF2308Q9RYFHDHKJAC
      where
        AD98OF2308Q9RYFHDHKJAC
      is the API key.
      
      Note that this random data being prepended is just a dirty workaround for
      the lack of random padding being used by the encryption format offered by
      rsa.repy or other repy libraries. This should be changed after a repy
      implementation of PKCS#1 is available.
    """
    try:
      assertions.assert_str(username)
    except AssertionError:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Username must be a string.")
    
    try:
      geniuser = interface.get_user_without_password(username)
    except DoesNotExistError:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Username does not exist.")
      
    # Don't change the number of bytes of random data without changing the API
    # spec and the xmlrpc client.
    randstring = ''.join(random.sample(string.letters + string.digits,
                                       ENCRYPTED_API_KEY_PADDING_BYTES)) 
    data = randstring + "!" + geniuser.api_key
    data = str(data) # make sure it's type str, not unicode, as required by rsa_encrypt
    user_pubkey_dict = rsa_string_to_publickey(geniuser.user_pubkey)
    encrypted_data = rsa_encrypt(data, user_pubkey_dict)
    # rsa_encrypt returns returns a string with an extra space in the front.
    encrypted_data = encrypted_data.strip() 
    # If the encrypted_data is more than one "block" long, something odd is
    # going on and there may be no padding applied to one or more encrypted
    # blocks.
    if ' ' in encrypted_data:
      raise InternalError("The encrypted_data to be returned by get_encrypted_api_key() " +
                          "was more than one block long. user: " + username + 
                          " encrypted_data: "+ encrypted_data)
    return encrypted_data



  @staticmethod
  @log_function_call_without_first_argument
  def regenerate_api_key(pwauth):
    """
    <Purpose>
      Regenerate a user's API key.This requires authenticating with the account
      password rather than the current API key.
    <Arguments>
      pwauth
        An authorization dict that includes a password instead of an apikey.
    <Exceptions>
      None.
    <Returns>
      The new API key.
    """
    geni_user = _pwauth(pwauth)
    return interface.regenerate_api_key(geni_user)



  @staticmethod
  @log_function_call_without_first_argument
  def set_public_key(pwauth, pubkeystring):
    """
    <Purpose>
      Sets the user account's public key. This requires authenticating with the
      account password rather than the current API key.
    <Arguments>
      pwauth
        An authorization dict that includes a password instead of an apikey.
      pubkeystring
        The account's new public key.
    <Exceptions>
      Raises xmlrpclib Fault Objects:
        FAULTCODE_INVALIDREQUEST if pubkey is invalid.
    <Returns>
      None.
    """
    geni_user = _pwauth(pwauth)
    try:
      interface.change_user_keys(geni_user, pubkeystring)
    except ValidationError, e:
      raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST, "Invalid public key: %s" % e)

    return 0



@log_function_call
def _auth(auth):
  """
  <Purpose>
    Internally used function that performs actual authorization.
  <Arguments>
    auth
      An authorization dict of the form {'username':username, 'api_key':api_key}
  <Exceptions>
    Raises xmlrpclib Fault Objects:
      FAULTCODE_INVALIDREQUEST if the auth dict is invalid.
      FAULTCODE_AUTHERROR if user auth fails.
  <Returns>
    On successful authentication, returns a geniuser object. Raises a fault otherwise.
  """
  if not isinstance(auth, dict):
    raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST,
                          "Auth dict must be a dictionary, not a " + str(type(auth)))
  
  try:
    username = auth['username']
    api_key = auth['api_key']
  except KeyError:
    raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST,
                          "Auth dict must contain both a 'username' and an 'api_key'.")
    
  try:
    geni_user = interface.get_user_with_api_key(username, api_key)
  except DoesNotExistError:
    raise xmlrpclib.Fault(FAULTCODE_AUTHERROR, "User auth failed.")
  
  return geni_user




def _pwauth(auth):
  """
  <Purpose>
    Internally used function that performs authorization based on the account
    password rather than the account api key.
  <Arguments>
    auth
      An authorization dict of the form {'username':username, 'password':password}
  <Exceptions>
    Raises xmlrpclib Fault Objects:
      FAULTCODE_INVALIDREQUEST if the auth dict is invalid.
      FAULTCODE_AUTHERROR if user auth fails.
  <Returns>
    On successful authentication, returns a geniuser object. Raises a fault otherwise.
  """
  if not isinstance(auth, dict):
    raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST,
                          "Auth dict must be a dictionary, not a " + str(type(auth)))
  
  try:
    username = auth['username']
    password = auth['password']
  except KeyError:
    raise xmlrpclib.Fault(FAULTCODE_INVALIDREQUEST,
                          "PasswordAuth dict must contain both a 'username' and an 'password'.")
    
  try:
    geni_user = interface.get_user_with_password(username, password)
  except DoesNotExistError:
    raise xmlrpclib.Fault(FAULTCODE_AUTHERROR, "User auth failed.")
  
  return geni_user
