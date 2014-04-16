
# The seattlegeni testlib must be imported first.
from seattlegeni.tests import testlib

from seattlegeni.tests import mocklib

from seattlegeni.common.api import maindb

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import validations

from seattlegeni.website.control import interface

import unittest



mocklib.mock_lockserver_calls()


good_username = "myusername"
good_password = "mypassword"
good_email = "example@example.com"
good_affiliation = "my affiliation"
good_pubkey = "400 401"


class SeattleGeniTestCase(unittest.TestCase):


  def setUp(self):
    # Setup a fresh database for each test.
    testlib.setup_test_db()



  def tearDown(self):
    # Cleanup the test database.
    testlib.teardown_test_db()



  def _create_user_expect_success(self, username, password=good_password, email=good_email, 
                                  affiliation=good_affiliation, pubkey=good_pubkey):
    
    # We expect a single key to be generated through the backed (the donor key)
    mocklib.mock_backend_generate_key(["1 2"])
    
    created_user = interface.register_user(username, password, email, affiliation, pubkey)
  
    user_from_db = maindb.get_user(username)
    assert(user_from_db.username == created_user.username)
    assert(user_from_db.email == created_user.email)
    assert(user_from_db.affiliation == created_user.affiliation)
    assert(user_from_db.user_pubkey == created_user.user_pubkey)
    assert(user_from_db.user_privkey == created_user.user_privkey)
    assert(user_from_db.donor_pubkey == created_user.donor_pubkey)
  
  
  
  def _create_user_expect_validation_error(self, username, password=good_password, email=good_email, 
                                  affiliation=good_affiliation, pubkey=good_pubkey):
    
    # An empty list because the ValidationError should occur before any backend
    # generate_key() calls are performed.
    mocklib.mock_backend_generate_key([])
    
    func = interface.register_user
    args = (username, password, email, affiliation, pubkey)
    self.assertRaises(ValidationError, func, *args)



  def test_username_minimum_length(self):
    username = "a" * validations.USERNAME_MIN_LENGTH
    userobj = self._create_user_expect_success(username)



  def test_username_too_short(self):
    username = "a" * (validations.USERNAME_MIN_LENGTH - 1)
    self._create_user_expect_validation_error(username)



  def test_username_maximum_length(self):
    username = "a" * validations.USERNAME_MAX_LENGTH
    userobj = self._create_user_expect_success(username)



  def test_username_too_long(self):
    username = "a" * (validations.USERNAME_MAX_LENGTH + 1)
    self._create_user_expect_validation_error(username)



  def test_username_invalid_chars_spaces(self):
    self._create_user_expect_validation_error("test user") # space in middle
    self._create_user_expect_validation_error(" testuser") # leading space
    self._create_user_expect_validation_error("testuser ") # trailing space



  def test_valid_chars_nonleading_underscores(self):
    self._create_user_expect_success("9test_user") 
    self._create_user_expect_success("test9user_") # one trailing underscore
    self._create_user_expect_success("testuser__") # two trailing underscores
    
    

  def test_username_invalid_chars_leading_underscores(self):
    username = "_testuser"
    self._create_user_expect_validation_error(username)



  def test_password_too_short(self):
    bad_password = "a" * (validations.PASSWORD_MIN_LENGTH - 1)
    self._create_user_expect_validation_error(good_username, password=bad_password)



  def test_password_same_as_username(self):
    self._create_user_expect_validation_error(good_username, password=good_username)



  def test_valid_country_email(self):
    email = "test@example.co.uk"
    self._create_user_expect_success(good_username, email=email)



  def test_valid_gmail_label_email(self):
    email = "test#label@gmail.com"
    self._create_user_expect_success(good_username, email=email)



  def test_invalid_email(self):
    bad_email = "test@test" # missing expected tld
    self._create_user_expect_validation_error(good_username, email=bad_email)



  def test_affiliation_too_short(self):
    bad_affiliation = "a" * (validations.AFFILIATION_MIN_LENGTH - 1)
    self._create_user_expect_validation_error(good_username, affiliation=bad_affiliation)



  def test_affiliation_too_long(self):
    bad_affiliation = "a" * (validations.AFFILIATION_MAX_LENGTH + 1)
    self._create_user_expect_validation_error(good_username, affiliation=bad_affiliation)



  def test_invalid_user_pubkey_empty_string(self):
    """
    Tests an empty string for the pubkey. It should be None rather than an
    empty string to indicate that we should generate the key for the user.
    """
    bad_pubkey = ""
    self._create_user_expect_validation_error(good_username, pubkey=bad_pubkey)
  
  
  
  def test_invalid_user_pubkey_invalid_key(self):
    bad_pubkey = "0" # should be two numbers
    self._create_user_expect_validation_error(good_username, pubkey=bad_pubkey)
   
    bad_pubkey = "1 0" # first number must be smaller than second
    self._create_user_expect_validation_error(good_username, pubkey=bad_pubkey)
  
    bad_pubkey = "a b" # letters, not numbers
    self._create_user_expect_validation_error(good_username, pubkey=bad_pubkey)
  
    bad_pubkey = "2 3 3" # they might have tried to upload their private key
    self._create_user_expect_validation_error(good_username, pubkey=bad_pubkey)


  
  def test_seattlegeni_generates_user_keypair(self):
    
    # We expect a single keypair to be generated directly through the keygen
    # api (specifically, the user keys).
    user_pubkey = "3 4"
    user_privkey = "2 3 3"
    mocklib.mock_keygen_generate_keypair([(user_pubkey, user_privkey)])
    
    # We expect a single key to be generated directly through the backed api
    # (specifically, the donor key).
    donor_pubkey = "1 2"
    mocklib.mock_backend_generate_key([donor_pubkey])
    
    provided_pubkey=None
    interface.register_user(good_username, good_password, good_email, 
                                           good_affiliation, provided_pubkey)

    user_from_db = maindb.get_user(good_username)

    assert(user_from_db.user_pubkey == user_pubkey)
    assert(user_from_db.user_privkey == user_privkey)
    assert(user_from_db.donor_pubkey == donor_pubkey)



# TODO: test the number of free vessel credits the user has after creation.
# TODO: test the number of used vessel credits the user has after creation.
# TODO: test the number of donations the user has after creation.
# TODO: test username exists




def run_test():
  unittest.main()



if __name__ == "__main__":
  run_test()
