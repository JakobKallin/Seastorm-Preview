"""
<Program>
  test_change_key.py

<Started>
  Oct 13, 2009

<Author>
  Justin Samuel

<Purpose>
  Tests that the change_key view function  handles normal operation and
  exceptions correctly.
  
<Notes>
  See test_register.py for an explanation of our usage of the Django test client.
"""

# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

import tempfile

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





def mock_noop(*args, **kwargs):
  pass
  
  
  
  

c = Client()

interface.change_user_keys = mock_noop





def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    login_test_user()
    
    test_regenerate_key()
    test_upload_key_no_file()
    test_upload_key_file()
    test_upload_key_file_empty_file()
    test_upload_key_file_invalid_key()
    
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()




def test_regenerate_key():
  """
  <Purpose>
    Tests submission of form to generate a new user key.
  """
  post_data = {'generate':'yes'}
  response = c.post('/html/change_key', post_data, follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  assert("Your new keys have been generated" in response.content)





def test_upload_key_no_file():
  """
  <Purpose>
    Tests submitting the upload key form with no key.
  """
  post_data = {}
  response = c.post('/html/change_key', post_data, follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/change_key.html")
  assert("You didn&#39;t select a public key file to upload" in response.content)





def test_upload_key_file():
  """
  <Purpose>
    Tests submitting the upload key form with no key.
  """
  uploaded_file = tempfile.NamedTemporaryFile(mode="w+")
  uploaded_file.write('1 2')
  uploaded_file.flush()
  uploaded_file.seek(0)

  post_data = {'pubkey':uploaded_file}
  response = c.post('/html/change_key', post_data, follow=True)
  
  uploaded_file.close()
  
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/profile.html")
  assert("Your public key has been successfully changed" in response.content)




def test_upload_key_file_empty_file():
  """
  <Purpose>
    Tests submitting the upload key form with no key.
  """
  uploaded_file = tempfile.NamedTemporaryFile(mode="w+")

  post_data = {'pubkey':uploaded_file}
  response = c.post('/html/change_key', post_data, follow=True)
  
  uploaded_file.close()
  
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/change_key.html")
  assert("Invalid file uploaded" in response.content)





def test_upload_key_file_invalid_key():
  """
  <Purpose>
    Tests submitting the upload key form with no key.
  """
  uploaded_file = tempfile.NamedTemporaryFile(mode="w+")
  uploaded_file.write('abc')
  uploaded_file.flush()
  uploaded_file.seek(0)

  post_data = {'pubkey':uploaded_file}
  response = c.post('/html/change_key', post_data, follow=True)
  
  uploaded_file.close()
  
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/change_key.html")
  assert("Invalid public key uploaded" in response.content)




  
# Creates a test user in the test db, and uses the test client to 'login',
# so all views that expect @login_required will now pass the login check. 
def login_test_user():
  # uses the mock get_logged_in_user function that represents a logged in user
  interface.get_logged_in_user = mock_get_logged_in_user
  
  user = DjangoUser.objects.create_user('tester', 'test@test.com', 'testpassword')
  user.save()
  c.login(username='tester', password='testpassword')



if __name__ == "__main__":
  main()
