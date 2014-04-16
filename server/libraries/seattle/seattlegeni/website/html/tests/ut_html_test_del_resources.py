"""
<Program>
  test_del_resources.py

<Started>
  8/30/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  Tests that the del_resource view function 
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

def mock_get_vessel_list(vesselhandle_list):
  return ['test', 'test2']

def mock_get_vessel_list_throws_DoesNotExistError(vesselhandle_list):
  raise DoesNotExistError

def mock_get_vessel_list_throws_InvalidRequestError(vesselhandle_list):
  raise InvalidRequestError

def mock_release_vessels(geniuser, vessel_list):
  pass

def mock_release_vessels_throws_InvalidRequestError(geniuser, vessel_list):
  raise InvalidRequestError

c = Client()
good_data = {'handle':'12345'}
interface.get_vessel_list = mock_get_vessel_list

def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    login_test_user()
    
    test_normal()
    test_get_vessel_list_throws_DoesNotExistError()
    test_get_vessel_list_throws_InvalidRequestError()
    test_release_vessels_throws_InvalidRequestError()
    
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()



def test_normal():
  """
  <Purpose>
    Tests normal behavior.
  """
  interface.get_vessel_list = mock_get_vessel_list
  interface.release_vessels = mock_release_vessels
  response = c.post('/html/del_resource', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert(response.template[0].name == 'control/myvessels.html')



def test_get_vessel_list_throws_DoesNotExistError():
  """
  <Purpose>
    Tests behavior if interface.get_vessel_list throws a DoesNotExistError
  """
  interface.get_vessel_list = mock_get_vessel_list_throws_DoesNotExistError
  interface.release_vessels = mock_release_vessels
  response = c.post('/html/del_resource', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert("Unable to remove" in response.content)
  assert(response.template[0].name == 'control/myvessels.html')



def test_get_vessel_list_throws_InvalidRequestError():
  """
  <Purpose>
    Tests behavior if interface.get_vessel_list throws an InvalidRequestError 
  """
  interface.get_vessel_list = mock_get_vessel_list_throws_InvalidRequestError
  interface.release_vessels = mock_release_vessels
  response = c.post('/html/del_resource', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert("Unable to remove" in response.content)
  assert(response.template[0].name == 'control/myvessels.html')



def test_release_vessels_throws_InvalidRequestError():
  """
  <Purpose>
    Tests behavior if interface.release_vessels throws an InvalidRequestError
  """
  interface.get_vessel_list = mock_get_vessel_list
  interface.release_vessels = mock_release_vessels_throws_InvalidRequestError
  response = c.post('/html/del_resource', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert("Unable to remove" in response.content)
  assert(response.template[0].name == 'control/myvessels.html')
  
  
  
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
