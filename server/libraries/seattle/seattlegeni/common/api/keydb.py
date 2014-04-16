"""
<Program>
  keydb.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
   This is the API that should be used to interact with the Key Database.
   Functions in this module are the only way that other code should interact
   with the Key Database.
   
   The init_keydb() method must be called before calling the other methods.
   
   For info on setting up and security access to the keydb, see the file
   seattlegeni/keydb/README.txt.
"""

import MySQLdb
import traceback

from seattlegeni.common.exceptions import *

from seattlegeni.common.util.assertions import *

from seattlegeni.keydb import config





def init_keydb():
  """
  <Purpose>
    Initialize the keydb api.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    Does nothing for the moment, actually. Maybe someday it will setup a
    connection pool or do other important initialization on the database.
    We can't just make a single connection and create a new cursor for
    each request because that's not how cursors work, at least with MySQLdb.
  <Returns>
    None
  """
  pass  





def _get_connection():
  try:
    return MySQLdb.connect(user=config.dbuser, passwd=config.dbpass, db=config.dbname, host=config.dbhost)
  except MySQLdb.Error:
    raise InternalError("Failed initializing key database: " + traceback.format_exc())





def _release_connection(connection):
  connection.close()





def get_private_key(pubkey):
  """
  <Purpose>
    Get a private key from the key database.
  <Arguments>
    pubkey
      The public key whose corresponding private key should be returned.
  <Exceptions>
    DoesNotExistError
      If there is no private key stored that corresponds to pubkey.
  <Side Effects>
    None
  <Returns>
    The private key that corresponds to pubkey.
  """
  
  assert_str(pubkey)
  
  connection = _get_connection()
  cursor = connection.cursor()
  
  try:
    try:
      # Note: `keys` is a reserved mysql keyword so must be quoted.
      cursor.execute("SELECT privkey FROM `keys` WHERE pubkey = %s", (pubkey))
    except MySQLdb.Error:
      raise InternalError("Failed getting private key: " + traceback.format_exc())
   
    if cursor.rowcount != 1:
      raise DoesNotExistError("No private key corresponding to the public key: " + pubkey)
    
    return cursor.fetchone()[0]
  
  finally:
    cursor.close()
    _release_connection(connection)





def set_private_key(pubkey, privkey, keydescription):
  """
  <Purpose>
    Store a private key in the key database.
  <Arguments>
    pubkey
      The public key to be stored.
    privkey
      The private key to be stored.
    keydescription
      A description of what this key is used for. E.g. "donor:[usernamehere]"
      to indicate the donor key for a specific user. This is non-critical and
      only because it may come in handy later.
  <Exceptions>
    None
  <Side Effects>
    A new record is added to the keys table in the key database with the
    information specified.
  <Returns>
    None
  """
  
  assert_str(pubkey)
  assert_str(privkey)
  assert_str(keydescription)
  
  connection = _get_connection()
  cursor = connection.cursor()
  
  try:
    try:
      # We insert include the pubkeyhash field to ensure that keys are unique.
      # We can't use the pubkey field because it is too long to enforce
      # uniqueness at the database level. We don't want to try to query it
      # ourselves because then we need to do two queries and have a shared access
      # lock around them, and that's a lot messier. This should be an uncommon
      # error case and likely means there's something very wrong in some other
      # part of the system, sothis is the simplest way to raise an exception if
      # this case does occur.
      # Note: `keys` is a reserved mysql keyword so must be quoted.
      cursor.execute("INSERT INTO `keys` (pubkeyhash, pubkey, privkey, description) VALUES (MD5(%s), %s, %s, %s)", 
                     (pubkey, pubkey, privkey, keydescription))
    except MySQLdb.Error:
      raise InternalError("Failed setting private key: " + traceback.format_exc())
  
  finally:
    cursor.close()
    _release_connection(connection)

