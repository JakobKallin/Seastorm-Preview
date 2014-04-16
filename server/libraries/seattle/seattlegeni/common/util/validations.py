"""
<Program>
  validations.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is a utility module to provide functions to valid user input for specific
  situations such as account registration. These methods raise a
  ValidationError if the value being checked is invalid. The message of the
  exceptions --- which is accessible with, for example str(e) --- will contain
  publicly-displayable information about why the validation failed. If the
  validation succeeds, nothing is returned.
"""

import re

from seattlegeni.common.exceptions import *

from seattlegeni.common.util.assertions import *

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")






USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 40
# In general, numbers, letters, and underscores are allowed in usernames.
USERNAME_ALLOWED_CHARS = r"0-9a-zA-Z_"
USERNAME_ALLOWED_REGEX = re.compile(r"^[" + USERNAME_ALLOWED_CHARS + "]+$")
# The first character of the username, however, we don't allow to be an underscore.
# We make this a separate regex so that it's easier to explain to the user
# if their username is denied.
USERNAME_ALLOWED_FIRST_CHARS = r"0-9a-zA-Z"
USERNAME_ALLOWED_FIRST_REGEX = re.compile(r"^[" + USERNAME_ALLOWED_FIRST_CHARS + "]")

PASSWORD_MIN_LENGTH = 6

# This regex is borrowed from http://www.regular-expressions.info/email.html
# It could probably be more restrictive and we'd be fine, but, really, if we're
# looking to ensure valid email addresses then we need to send confirmation
# emails.
EMAIL_VALID_REGEX = re.compile(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")

AFFILIATION_MIN_LENGTH = 3
AFFILIATION_MAX_LENGTH = 200





def validate_username(username):
  """
  <Purpose>
    Determine whether username is a valid username.
  """
  try:
    assert_str(username)
  except AssertionError:
    raise ValidationError("Username must be a string.")
  
  if len(username) < USERNAME_MIN_LENGTH:
    raise ValidationError("Username must be at least " + str(USERNAME_MIN_LENGTH) + " characters.")
  
  if len(username) > USERNAME_MAX_LENGTH:
    raise ValidationError("Username must be less than " + str(USERNAME_MAX_LENGTH) + " characters.")
  
  if not USERNAME_ALLOWED_REGEX.match(username):
    raise ValidationError("Username can only contain the characters " + USERNAME_ALLOWED_CHARS)

  if not USERNAME_ALLOWED_FIRST_REGEX.match(username):
    raise ValidationError("Username must start with one of the characters " + USERNAME_ALLOWED_FIRST_CHARS)





def validate_password(password):
  """
  <Purpose>
    Determine whether password is a valid (strong enough) password. The code that
    calls this function should probably also make sure that the password isn't
    the same as the username.
  """
  try:
    assert_str(password)
  except AssertionError:
    raise ValidationError("Password must be a string.")
  
  if len(password) < PASSWORD_MIN_LENGTH:
    raise ValidationError("Password must be at least " + str(PASSWORD_MIN_LENGTH) + " characters.")





def validate_username_and_password_different(username, password):
  """
  <Purpose>
    Determine whether username is different enough from the password.
  """
  try:
    assert_str(username)
    assert_str(password)
  except AssertionError:
    raise ValidationError("Username and password must be strings.")
  
  if username == password:
    raise ValidationError("Username cannot be the same as the password.")





def validate_email(email):
  """
  <Purpose>
    Determine whether email is a valid email address.
  """
  try:
    assert_str(email)
  except AssertionError:
    raise ValidationError("E-mail must be a string.")
  
  if not EMAIL_VALID_REGEX.match(email):
    raise ValidationError("E-mail address is not valid.")





def validate_affiliation(affiliation):
  """
  <Purpose>
    Determine whether affiliation is a valid affiliation.
  """
  try:
    assert_str(affiliation)
  except AssertionError:
    raise ValidationError("Affiliation must be a string.")
  
  if len(affiliation) < AFFILIATION_MIN_LENGTH:
    raise ValidationError("Affiliation must be at least " + str(AFFILIATION_MIN_LENGTH) + " characters.")
  
  if len(affiliation) > AFFILIATION_MAX_LENGTH:
    raise ValidationError("Affiliation must be less than " + str(AFFILIATION_MAX_LENGTH) + " characters.")





def validate_pubkey_string(pubkeystring):
  """
  <Purpose>
    Determine whether a pubkey string looks like a valid public key.
  <Arguments>
    pubkeystring
      The string we want to find out if it is a valid pubkey string.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    True if pubkeystring looks like a valid pubkey, False otherwise.
    Currently this uses functions that aren't conclusive about validity of the
    key, but for our purposes we just want to make sure it's generally the
    correct data format.
  """
  try:
    assert_str(pubkeystring)
  except AssertionError:
    raise ValidationError("Public key must be a string.")
  
  try:
    possiblepubkey = rsa_string_to_publickey(pubkeystring)
  except ValueError:
    raise ValidationError("Public key is not of a correct format.")

  if not rsa_is_valid_publickey(possiblepubkey):
    raise ValidationError("Public key is invalid.")


