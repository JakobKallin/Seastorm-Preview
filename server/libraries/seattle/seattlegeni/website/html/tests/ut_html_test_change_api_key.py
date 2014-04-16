"""
<Program>
  test_view_change_api_key.py

<Started>
  Oct 16, 2009

<Author>
  Justin Samuel

<Purpose>
  Tests that the api_info view function which is responsible for displaying and
  handling requests to regenerate the user's api key.
  
<Notes>
  See test_register.py for an explanation of our usage of the Django test client.
"""

#pragma out

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

interface.regenerate_api_key = mock_noop





def main():
  
  # Setup test environment
  testlib.setup_test_environment()
  testlib.setup_test_db()
  
  try:
    login_test_user()
    test_regenerate_api_key()
    print "All tests passed."
    
  finally:
    testlib.teardown_test_db()
    testlib.teardown_test_environment()





def test_regenerate_api_key():
  """
  <Purpose>
    Tests submission of form to generate a new api key.
  """
  post_data = {'generate_api_key':'yes'}
  response = c.post('/html/api_info', post_data, follow=True)
  assert(response.status_code == 200)
  assert(response.template[0].name == "control/api_info.html")
  assert("Your API key has been regenerated" in response.content)





  
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
