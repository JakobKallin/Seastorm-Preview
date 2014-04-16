"""
<Program>
  test_urls.py

<Started>
  Oct 13, 2009

<Author>
  Justin Samuel

<Purpose>
  
<Notes>
  Uses a Django test client, not our xmlrpc client. This is intentional.
  The xmlrpc client should be tested separately.
"""

#pragma out
#pragma error OK


# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

import xmlrpclib
import unittest

from django.contrib.auth.models import User as DjangoUser

from seattlegeni.common.exceptions import *

from seattlegeni.common.api import maindb

from seattlegeni.website.xmlrpc import views

from seattlegeni.website.xmlrpc.tests import xmlrpctestutil

from seattlegeni.website.control import interface
from seattlegeni.website.control import models

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")




def mock_raises_DoesNotExistError(*args, **kwargs):
  raise DoesNotExistError



def mock_raises_InvalidRequestError(*args, **kwargs):
  raise InvalidRequestError



def mock_raises_InsufficientUserResourcesError(*args, **kwargs):
  raise InsufficientUserResourcesError



def mock_raises_UnableToAcquireResourcesError(*args, **kwargs):
  raise UnableToAcquireResourcesError



def mock_noop(*args, **kwargs):
  pass



def mock_interface_get_user_with_api_key(username, api_key):
  geniuser = models.GeniUser(username=username, password="password", email='test@test.com',
                             affiliation='test affil', user_pubkey='user_pubkey',
                             user_privkey='user_privkey', donor_pubkey='donor_pubkey',
                             usable_vessel_port='12345', free_vessel_credits=10)
  geniuser.api_key = api_key
  # Not saving the geniuser record, we're not trying to interact with the db.
  return geniuser



def mock_interface_get_user_with_password(username, password):
  geniuser = models.GeniUser(username=username, password=password, email='test@test.com',
                             affiliation='test affil', user_pubkey='user_pubkey',
                             user_privkey='user_privkey', donor_pubkey='donor_pubkey',
                             usable_vessel_port='12345', free_vessel_credits=10)
  geniuser.password = password
  # Not saving the geniuser record, we're not trying to interact with the db.
  return geniuser



def create_mock_get_user(username, password="testpassword", api_key="testapikey",
                         pubkeystr="pubkeystr", privkeystr="privkeystr"):
  
  geniuser = models.GeniUser(username=username, password=password, email='test@test.com',
                             affiliation='test affil', user_pubkey=pubkeystr,
                             user_privkey=privkeystr, donor_pubkey='donor_pubkey',
                             usable_vessel_port='12345', free_vessel_credits=10,
                             api_key = api_key)
  # Not saving the geniuser record, we're not trying to interact with the db.

  def mock_interface_get_user(username, *args, **kwargs):
    return geniuser

  return mock_interface_get_user



def mock_interface_get_vessel_list(vesselhandle_list):
  return []



def mock_interface_get_vessel_infodict_list(vessel_list):
  return []


def mock_interface_regenerate_api_key(geniuser):
  return "a" * maindb.API_KEY_LENGTH


def mock_interface_change_user_keys(geniuser, pubkeystring):
  pass


proxy = xmlrpclib.ServerProxy('http://fakehost/xmlrpc/',
                              transport=xmlrpctestutil.TestTransport())




class SeattleGeniTestCase(unittest.TestCase):


  def setUp(self):
    # Indicate a user record was found with the provided auth info.
    interface.get_user_with_api_key = mock_interface_get_user_with_api_key
    interface.get_user_with_password = mock_interface_get_user_with_password


  def tearDown(self):
    pass



  def test_invalid_auth_dict(self):
    
    auth = 'not a dict'
    
    try:
      proxy.get_account_info(auth)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    auth = {'username':'tester'}
    
    try:
      proxy.get_account_info(auth)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    
    
  def test_all_functions_auth_failure(self):
    """
    Make sure all of the xmlrpc calls raise an exception if the auth check
    fails.
    """
    
    auth = {'username':'tester', 'api_key':'api_key'}

    # Indicate no user record was found with the provided auth info.
    interface.get_user_with_api_key = mock_raises_DoesNotExistError
    
    try:
      proxy.renew_resources(auth, [])
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")
    
    try:
      proxy.acquire_resources(auth, {})
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")
      
    try:
      proxy.acquire_specific_vessels(auth, [])
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")
    
    try:
      proxy.release_resources(auth, [])
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")

    try:
      proxy.get_resource_info(auth)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")

    try:
      proxy.get_account_info(auth)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")

    try:
      proxy.get_public_key(auth)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_AUTHERROR)
    else:
      self.fail("Expected an exception.")

    

  def test_renew_resources_invalid_vessel_handle_list(self):
    
    auth = {'username':'tester', 'api_key':'api_key'}

    vesselhandle_list = {'dict not a list':'123'}
    
    try:
      proxy.renew_resources(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")


  
  def test_renew_resources(self):
    
    auth = {'username':'tester', 'api_key':'api_key'}
    vesselhandle_list = ['vessel1', 'vessel2']
    
    # Check successful case. Returns a zero to indicate success.
    
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.renew_vessels = mock_noop
    
    response = proxy.renew_resources(auth, vesselhandle_list)
    self.assertEqual(response, 0)
    
    # Check various error cases. These all return FAULTCODE_INVALIDREQUEST.
    
    interface.get_vessel_list = mock_raises_DoesNotExistError
    interface.renew_vessels = mock_noop
    
    try:
      proxy.renew_resources(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    interface.get_vessel_list = mock_raises_InvalidRequestError
    interface.renew_vessels = mock_noop
    
    try:
      proxy.renew_resources(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
  
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.renew_vessels = mock_raises_InvalidRequestError
    
    try:
      proxy.renew_resources(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    # This is the case where the user has less credits than acquired resources.
    
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.renew_vessels = mock_raises_InsufficientUserResourcesError
    
    try:
      proxy.renew_resources(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_NOTENOUGHCREDITS)
    else:
      self.fail("Expected an exception.")


  
  def test_acquire_resources_rspecs(self):
    
    auth = {'username':'tester', 'api_key':'api_key'}
    vesselhandle_list = ['vessel1', 'vessel2']
    
    rspec_valid = {'rspec_type':'random', 'number_of_nodes':2}
    
    # invalid rspecs
    rspec_negativenodes = {'rspec_type':'random', 'number_of_nodes':-10}
    rspec_invalid_rtype = {'rspec_type':'wtf', 'number_of_nodes':10}
    rspec_badtype = {'rspec_type':42, 'number_of_nodes':'a string'}
    rspec_empty = {'rspec_type':'', 'number_of_nodes':0}
    rspec_missingkey = {'number_of_nodes':10}
    rspec_badkeys = {'bad':'', 'keys':''}
    
    try:
      proxy.acquire_resources(auth, rspec_negativenodes)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
      
    try:
      proxy.acquire_resources(auth, rspec_invalid_rtype)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    try:
      proxy.acquire_resources(auth, rspec_badtype)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
      
    try:
      proxy.acquire_resources(auth, rspec_empty)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    try:
      proxy.acquire_resources(auth, rspec_missingkey)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
    
    try:
      proxy.acquire_resources(auth, rspec_badkeys)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")
      
    # This is the case where the user has less credits than the number of
    # vessels they are trying to acquire.
    
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.acquire_vessels = mock_raises_InsufficientUserResourcesError
    
    try:
      proxy.acquire_resources(auth, rspec_valid)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_NOTENOUGHCREDITS)
    else:
      self.fail("Expected an exception.")
      
    # This is the case where SeattleGENI doesn't have enough resources to
    # acquire the requested vessels.

    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.acquire_vessels = mock_raises_UnableToAcquireResourcesError
    
    try:
      proxy.acquire_resources(auth, rspec_valid)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_UNABLETOACQUIRE)
    else:
      self.fail("Expected an exception.")



  def test_acquire_specific_vessels(self):
    
    auth = {'username':'tester', 'api_key':'api_key'}
    vesselhandle_list = ['vessel1', 'vessel2']
    
    # Check successful case. Returns a zero to indicate success.
    
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.get_vessel_infodict_list = mock_interface_get_vessel_infodict_list
    interface.acquire_specific_vessels = mock_noop
    
    response = proxy.acquire_specific_vessels(auth, vesselhandle_list)
    self.assertTrue(isinstance(response, list))
    
    # vesselhandle_list is not a list.
    try:
      proxy.acquire_specific_vessels(auth, 1)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_INVALIDREQUEST)
    else:
      self.fail("Expected an exception.")

    # This is the case where the user has less credits than the number of
    # vessels they are trying to acquire.
    
    interface.get_vessel_list = mock_interface_get_vessel_list
    interface.acquire_specific_vessels = mock_raises_InsufficientUserResourcesError
    
    try:
      proxy.acquire_specific_vessels(auth, vesselhandle_list)
    except xmlrpclib.Fault, e:
      self.assertEqual(e.faultCode, views.FAULTCODE_NOTENOUGHCREDITS)
    else:
      self.fail("Expected an exception.")



  def test_get_encrypted_api_key(self):
    
    username = "testuser"
    api_key = "testapikey"
    
    (pubkeydict, privkeydict) = rsa_gen_pubpriv_keys(512)
    pubkeystr = rsa_publickey_to_string(pubkeydict)
    privkeystr = rsa_privatekey_to_string(privkeydict)
    
    interface.get_user_without_password = create_mock_get_user(username, api_key=api_key,
                                                               pubkeystr=pubkeystr,
                                                               privkeystr=privkeystr)
    
    response = proxy.get_encrypted_api_key(username)
    self.assertTrue(isinstance(response, str))
    
    encrypted_data = proxy.get_encrypted_api_key(username)
    decrypted_data = rsa_decrypt(encrypted_data, privkeydict)
    split_data = decrypted_data.split("!")
    
    self.assertEqual(api_key, split_data[1])



  def test_regenerate_api_key(self):
    
    username = "testuser"
    password = "testpassword"
    original_api_key = "original_api_key"
    
    interface.get_user_without_password = create_mock_get_user(username, password=password,
                                                               api_key=original_api_key)
    interface.regenerate_api_key = mock_interface_regenerate_api_key
    
    pwauth = {"username" : username, "password" : password}
    
    response = proxy.regenerate_api_key(pwauth)
    self.assertTrue(isinstance(response, str))
    self.assertNotEqual(response, original_api_key)
    self.assertEqual(len(response), maindb.API_KEY_LENGTH)



  def test_set_public_key(self):
    
    username = "testuser"
    password = "testpassword"
    original_api_key = "original_api_key"
    
    interface.get_user_without_password = create_mock_get_user(username, password=password,
                                                               api_key=original_api_key)
    interface.change_user_keys = mock_interface_change_user_keys
    
    pwauth = {"username" : username, "password" : password}
    
    (pubkeydict, privkeydict) = rsa_gen_pubpriv_keys(512)
    pubkeystr = rsa_publickey_to_string(pubkeydict)
    
    proxy.set_public_key(pwauth, pubkeystr)



def main():
  # The tests don't use the database, so we just make a single database
  # so that it exists to prevent unrelated errors when we use the models.
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    unittest.main()
  
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()



if __name__ == "__main__":
  main()
