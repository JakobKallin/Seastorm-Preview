"""
<Program>
  test_get_resources.py

<Started>
  8/30/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  Tests that the get_resources view function 
  handles normal operation and exceptions correctly.
  
<Notes>
  See test_register.py for an explanation of our usage of the Django test client.
"""

#pragma out


# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

from seattlegeni.common.exceptions import *
from seattlegeni.website.control import interface
from seattlegeni.website.control import models

from django.contrib.auth.models import User as DjangoUser

# The django test client emulates a webclient, and returns what django
# considers the final rendered result (in HTML). This allows to test purely the view
# functions. 
from django.test.client import Client


# Declare our mock functions
def mock_get_logged_in_user(request):
  geniuser = models.GeniUser(username='tester', password='password', email='test@test.com',
                             affiliation='test affil', user_pubkey='user_pubkey',
                             user_privkey='user_privkey', donor_pubkey='donor_pubkey',
                             usable_vessel_port='12345', free_vessel_credits=10)
  return geniuser

def mock_acquire_vessels(geniuser, vesselcount, vesseltype):
  return ['test1', 'test2']

def mock_acquire_vessels_throws_UnableToAcquireResourcesError(geniuser, vesselcount, vesseltype):
  raise UnableToAcquireResourcesError

def mock_acquire_vessels_throws_InsufficientUserResourcesError(geniuser, vesselcount, vesseltype):
  raise InsufficientUserResourcesError

c = Client()
good_data = {'num':5, 'env':'rand'}


def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    login_test_user()
    
    test_normal()
    test_interface_throws_UnableToAcquireResourcesError()
    test_interface_throws_InsufficientUserResourcesError()
    test_blank_POST_data()
    test_invalid_POST_data_invalid_num()
    test_invalid_POST_data_invalid_env()
    
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()



def test_normal():
  """
  <Purpose>
    Test normal behavior
  """
  interface.acquire_vessels = mock_acquire_vessels
  response = c.post('/html/get_resources', good_data, follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')


def test_interface_throws_UnableToAcquireResourcesError():
  """
  <Purpose>
    Test behavior if interface throws UnableToAcquireResourcesError.
  
  <Note>
    Checking only the existance of "action_summary" in the response
    is sufficient in seeing whether the view caught the error, since 
    error messages are shown in that html element. (Of course, so are
    normal messages, but we are clearly having the interface throw an
    exception, so normal messages don't even exist in this context).
  """
  interface.acquire_vessels = mock_acquire_vessels_throws_UnableToAcquireResourcesError
  response = c.post('/html/get_resources', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')
  assert("Unable to acquire vessels at this time" in response.content)



def test_interface_throws_InsufficientUserResourcesError():
  """
  <Purpose>
    Test behavior if interface throws InsufficientUserResourcesError.
  """
  interface.acquire_vessels = mock_acquire_vessels_throws_InsufficientUserResourcesError
  response = c.post('/html/get_resources', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')
  assert("Unable to acquire" in response.content)
  assert("vessel credit" in response.content)



def test_blank_POST_data():
  """
  <Purpose>
    Test behavior if we submit blank POST data.
  """
  interface.acquire_vessels = mock_acquire_vessels
  response = c.post('/html/get_resources', {}, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')
  assert("This field is required" in response.content)



def test_invalid_POST_data_invalid_num():
  """
  <Purpose>
    Test behavior if we submit POST data with an invalid 'num' field.
  """
  interface.acquire_vessels = mock_acquire_vessels
  test_data = {'num':-5, 'env':'rand'}
  response = c.post('/html/get_resources', test_data, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')
  assert("Select a valid choice" in response.content)



def test_invalid_POST_data_invalid_env():
  """
  <Purpose>
    Test behavior if we submit POST data with an invalid 'env' field.
  """
  interface.acquire_vessels = mock_acquire_vessels
  test_data = {'num':5, 'env':'notvalid'}
  response = c.post('/html/get_resources', test_data, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')
  assert("Select a valid choice" in response.content)



# Creates a test user in the test db, and uses the test client to 'login',
# so all views that expect @login_required will now pass the login check. 
def login_test_user():
  # uses the mock get_logged_in_user function that represents a logged in user
  interface.get_logged_in_user = mock_get_logged_in_user
  
  user = DjangoUser.objects.create_user('tester', 'test@test.com', 'testpassword')
  user.save()
  c.login(username='tester', password='testpassword')



if __name__=="__main__":
  main()