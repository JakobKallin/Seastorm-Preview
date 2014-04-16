"""
<Program>
  test_register.py

<Started>
  8/26/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  Tests the registration function of the HTML frontend view.

<Notes>
  We make use of the Django test client, which emulates a webclient and returns what django
  considers the final rendered result (in HTML). This allows us to test purely the view functions.
  Apart from testing the validity/sanity of the view functions, we also mock-out all calls into the
  interface, and return test values to the view functions. This way, we can ensure that the views behave
  properly in normal (and abnormal) interactions with the interface.
"""

# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

import StringIO
import os

from seattlegeni.common.exceptions import *
from seattlegeni.common.util import validations
from seattlegeni.website.control import interface
from seattlegeni.website.control import models
from seattlegeni.website.html import forms

from django.contrib.auth.models import User as DjangoUser

# The django test client emulates a webclient, and returns what django
# considers the final rendered result (in HTML). This allows to test purely the view
# functions. 
from django.test.client import Client


# Declare our mock functions
def mock_register_user(username, password, email, affiliation, pubkey=None):
  testuser = DjangoUser()
  testuser.username = "test_user"
  return testuser

def mock_register_user_throws_ValidationError(username, password, email, affiliation, pubkey=None):
  raise ValidationError

def mock_get_logged_in_user(request):
  raise DoesNotExistError

# set up test data
c = Client()
good_data = {'username': 'tester', 
             'password1': '12345678',
             'password2': '12345678',  
             'email': 'test@test.com',  
             'affiliation': 'test affil', 
             'gen_upload_choice':'1'}

test_data = {}

def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    # mock out interface calls
    interface.register_user = mock_register_user
    interface.get_logged_in_user = mock_get_logged_in_user
    
    # run tests
    test_post_blank_form()
    test_short_username()
    test_long_username()
    test_invalid_username()
    test_short_password()
    test_nonmatching_password()
    test_matching_username_password()
    test_short_affil()
    test_long_affil()
    test_invalid_email()
    test_key_upload_with_no_file()
    test_key_upload_with_oversized_file()
    test_key_upload_with_bad_format_key()
    test_key_upload_with_valid_key()
    test_normal()
    
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()

  

def test_post_blank_form():
  """
  <Purpose>
    Test for posting blank form
  
  <Note>
    Checking for the existance of (p class=\"warning\") in response.content is
    sufficient in detecting whether the view caught an error; since the page
    will only ever show that html element in the event of an error. And, this 
    is all we care about: that the page recognized that bad data was passed in, 
    and an error was raised.
  """
  response = c.post('/html/register', {'username': '', 
                                       'password1':'', 
                                       'password2':'', 
                                       'email':'', 
                                       'affiliation':'', 
                                       'gen_upload_choice':'1'}, follow=True)
  
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_short_username():
  """
  <Purpose>
    Test for username too short
  """  
  shortuser = ""
  for n in range(0, validations.USERNAME_MIN_LENGTH - 1):
    shortuser += "a"
  
  test_data = good_data.copy()
  test_data['username'] = shortuser
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_long_username():
  """
  <Purpose>
    Test for username too long
  """  
  longuser = ""
  for n in range(0, validations.USERNAME_MAX_LENGTH + 1):
    longuser += "a"
  
  test_data = good_data.copy()
  test_data['username'] = longuser
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_invalid_username():
  """
  <Purpose>
    Test for invalid username
  """  
  test_data = good_data.copy()
  test_data['username'] = 'tester!!!'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_short_password():
  """
  <Purpose>
    Test for password too short
  """  
  test_data = good_data.copy()
  test_data['password1'] = '12345'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_nonmatching_password():
  """
  <Purpose>
    Test for non-matching passwords
  """  
  test_data = good_data.copy()
  test_data['password2'] = '87654321'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_matching_username_password():
  """
  <Purpose>
    Test for same username and password
  """  
  test_data = good_data.copy()
  test_data['username'] = 'tester'
  test_data['password1'] = 'tester'
  test_data['password2'] = 'tester'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_short_affil():
  """
  <Purpose>
    Test for affiliation too short
  """  
  shortaffil = ""
  for n in range(0, validations.AFFILIATION_MIN_LENGTH - 1):
    shortaffil += "a"
  
  test_data = good_data.copy()
  test_data['affiliation'] = shortaffil
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_long_affil():
  """
  <Purpose>
    Test for affiliation too long
  """  
  longaffil = ""
  for n in range(0, validations.AFFILIATION_MAX_LENGTH + 1):
    longaffil += "a"
  
  test_data = good_data.copy()
  test_data['affiliation'] = longaffil
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_invalid_email():
  """
  <Purpose>
    Test for invalid e-mail
  """  
  test_data = good_data.copy()
  test_data['email'] = 'invalid@email'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_key_upload_with_no_file():
  """
  <Purpose>
    Test key upload with no file
  """  
  test_data = good_data.copy()
  test_data['gen_upload_choice'] = '2'
  
  response = c.post('/html/register', test_data, follow=True)
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_key_upload_with_oversized_file():
  """
  <Purpose>
    Test key upload with oversized file
  """  
  test_data = good_data.copy()
  test_data['gen_upload_choice'] = '2'
  
  # set up a temporary 'key' file object
  data = ''
  for n in range(0, forms.MAX_PUBKEY_UPLOAD_SIZE + 1):
    data += '0'
  
  fh = open(os.path.join(os.getcwd(), 'bigkey'), 'w')
  fh.write(data)
  fh.close()
  fh = open('bigkey')
  test_data['pubkey'] = fh
  
  response = c.post('/html/register', test_data, follow=True)
  fh.close()
  os.remove(os.path.join(os.getcwd(), 'bigkey'))
  
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_key_upload_with_bad_format_key():
  """
  <Purpose>
    Test key upload with badly formatted key
  """  
  test_data = good_data.copy()
  test_data['gen_upload_choice'] = '2'
  
  data = 'this is a fake key'
  fh = open(os.path.join(os.getcwd(), 'fakekey'), 'w')
  fh.write(data)
  fh.close()
  fh = open('fakekey')
  test_data['pubkey'] = fh
  
  response = c.post('/html/register', test_data, follow=True)
  fh.close()
  os.remove(os.path.join(os.getcwd(), 'fakekey'))
  
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_key_upload_with_valid_key():
  """
  <Purpose>
    Test key upload with valid key
  """  
  test_data = good_data.copy()
  test_data['gen_upload_choice'] = '2'
  
  data = '65537 1255529510320394315881981094520474315188224118590997402913761676258431241305254181126132200564438402053537493727356349330161335739149834523475129922460441305694528141374947142391183883986671526830986555904385942930184161960677388507'
  fh = open(os.path.join(os.getcwd(), 'goodkey'), 'w')
  fh.write(data)
  fh.close()
  fh = open('goodkey')
  test_data['pubkey'] = fh
  
  response = c.post('/html/register', test_data, follow=True)
  fh.close()
  os.remove(os.path.join(os.getcwd(), 'goodkey'))
  
  assert(response.status_code == 200)
  assert("successfully registered" in response.content)



def test_interface_throws_ValidationError():
  """
  <Purpose>
    Test behavior if interface throws a ValidationError, 
    even after passing all validation
  """  
  interface.register_user = mock_register_user_throws_ValidationError
  response = c.post('/html/register', good_data, follow=True)
  
  assert(response.status_code == 200)
  assert("p class=\"warning\"" in response.content)



def test_normal():
  """
  <Purpose>
    Test normal behavior
  """  
  interface.register_user = mock_register_user
  response = c.post('/html/register', good_data, follow=True)
  
  # check that the view thinks the user has been registered
  assert(response.status_code == 200)
  assert("successfully registered" in response.content)
  
  # check that the current page is now the login page
  assert(response.template[0].name == "accounts/login.html")


if __name__=="__main__":
  main()