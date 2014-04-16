"""
<Program>
  test_urls.py

<Started>
  8/28/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  Tests that all site urls are being *served* correctly.
  This means that all urls eventually return an HTTP 200 OK, and that 
  non-logged-in, and logged-in users are being redirected to correct pages.

  Note that just because the pages are being served correctly does
  not imply that they *function* correctly. Make sure all other tests
  are run as well, to test the functional correctness of pages.
  
<Notes>
  See test_register.py for an explanation of our usage of the Django test client.
"""

#pragma out

import datetime

# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

from seattlegeni.common.exceptions import *
from seattlegeni.website.control import interface
from seattlegeni.website.control import models
from seattlegeni.website.html import forms

from django.contrib.auth.models import User as DjangoUser

# The django test client emulates a webclient, and returns what django
# considers the final rendered result (in HTML). This allows to test purely the view
# functions. 
from django.test.client import Client



# Declare our mock functions
def mock_get_logged_in_user_throws_DoesNotExistError(request):
  raise DoesNotExistError

def mock_get_logged_in_user(request):
  geniuser = models.GeniUser(username='tester', password='password', email='test@test.com',
                             affiliation='test affil', user_pubkey='user_pubkey',
                             user_privkey='user_privkey', donor_pubkey='donor_pubkey',
                             usable_vessel_port='12345', free_vessel_credits=10)
  return geniuser

def mock_get_total_vessel_credits(geniuser):
  return 10

def mock_get_acquired_vessels(geniuser):
  return ['test', 'test2']

def mock_get_vessel_infodict_list(vessel_list):
  # At a minimum, the expires_in_seconds key must exist because it is used by
  # the myvessels view.
  return [{'expires_in_seconds':1}, 
          {'expires_in_seconds':2}]

def mock_delete_private_key(user):
  pass

# Mock out interface calls
#interface.get_logged_in_user = mock_get_logged_in_user
interface.get_total_vessel_credits = mock_get_total_vessel_credits
interface.get_acquired_vessels = mock_get_acquired_vessels
interface.get_vessel_infodict_list = mock_get_vessel_infodict_list
interface.delete_private_key = mock_delete_private_key

c = Client()



def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    # Run tests
    get_pages_without_user_logged_in()
    get_pages_with_user_logged_in()
    
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()



def get_pages_without_user_logged_in():
  # uses the mock get_logged_in_user function that represents no logged in user
  interface.get_logged_in_user = mock_get_logged_in_user_throws_DoesNotExistError
  
  response = c.get('/html/register', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/register.html")
  
  response = c.get('/html/login', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/logout', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/accounts_help', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/help.html")
  
  # The URLs we tell the user to distribute have "download" instead of "html"
  # in them.
  response = c.get('/download/tester/', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "download/installers.html")
  
  # The following pages should all bounce back to the login page,
  # since there is no user logged in currently.
  response = c.get('/html/profile', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/mygeni', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/myvessels', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/help', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/getdonations', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/get_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/del_resource', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/del_all_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/renew_resource', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/renew_all_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  # POST is required for deleting private key.
  response = c.get('/html/del_priv', follow=True)
  assert(response.status_code == 405)
  
  response = c.get('/html/priv_key', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")
  
  response = c.get('/html/pub_key', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")

  response = c.get('/html/change_key', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")

  response = c.get('/html/api_info', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "accounts/login.html")





def get_pages_with_user_logged_in():
  _login_test_user()
  
  response = c.get('/html/register', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  
  response = c.get('/html/login', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  
  response = c.get('/html/profile', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  
  response = c.get('/html/mygeni', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/mygeni.html")
  
  response = c.get('/html/myvessels', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/help', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/help.html")
  
  response = c.get('/html/getdonations', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/getdonations.html")
  
  ##########################################################################
  # the following pages expect POST requests. when they see a GET request, #
  # they should bounce the user back to the 'My Vessels' page              #
  ##########################################################################
  response = c.get('/html/get_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/del_resource', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/del_all_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/renew_resource', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/renew_all_resources', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/myvessels.html")
  
  response = c.get('/html/api_info', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/api_info.html")
  assert("Your API key is" in response.content)
  
  ##########################################################################
  
  # The change_key page accepts either GET or POST. If it is a GET request,
  # the the forms for changing keys are displayed. If it is a POST and the
  # POST is valid (either a request to generate new keys or upload of a key),
  # the user is shown the profile. If it is an invalid POST, then the same
  # page is redisplayed with a message.
  
  response = c.get('/html/change_key', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/change_key.html")

  # Empty post data is invalid.
  response = c.post('/html/change_key', {}, follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/change_key.html")
  
  ##########################################################################
  
  # POST is required for deleting private key.
  response = c.get('/html/del_priv', follow=True)
  assert(response.status_code == 405)
  
  response = c.post('/html/del_priv', follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  assert("Your private key has been deleted" in response.content)
  
  # Make sure that priv_key returns an attachment response
  response = c.get('/html/priv_key', follow=True)
  assert(response.status_code == 200)
  assert("attachment" in response['Content-Disposition'])
  assert(".privatekey" in response['Content-Disposition'])
  
  # Make sure that pub_key returns an attachment response
  response = c.get('/html/pub_key', follow=True)
  assert(response.status_code == 200)
  assert("attachment" in response['Content-Disposition'])
  assert(".publickey" in response['Content-Disposition'])

  # Logging out should return an HttpResponseRedirect to login
  response = c.get('/html/logout', follow=True)
  assert(response.status_code == 302)
  assert("/html/login" in response['Location'])





def _login_test_user():
  """
  <Purpose>
    Creates a test user in the test db, and uses the test client to 'login',
    so all views that expect @login_required will now pass the login check. 
  """
  # uses the mock get_logged_in_user function that represents a logged in user
  interface.get_logged_in_user = mock_get_logged_in_user
  
  user = DjangoUser.objects.create_user('tester', 'test@test.com', 'testpassword')
  user.save()
  c.login(username='tester', password='testpassword')
  

if __name__=="__main__":
  main()