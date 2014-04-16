"""
<Program>
  keygen.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
   This is the API that should be used to generate new public/private key pairs.
"""

import traceback

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import log

from seattlegeni.common.util.decorators import log_function_call_without_return

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")






# Set to True to obtain keys from the key daemon, false to generate keys
# directly (potentially making some parts of seattlegeni run very slow).
USE_KEYDAEMON = False

KEYDAEMON_HOST = "127.0.0.1"

KEYDAEMON_PORT = "8030"

# If USE_KEYDAEMON is False and so we manually/directly generate keys, this
# is the bit size of the keys we generate.
MANUAL_GENERATION_BITSIZE = 1024





@log_function_call_without_return
def generate_keypair():
  """
  <Purpose>
    Obtain a new (unused) public/private keypair.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    Requests a key from the keygen daemon if USE_KEYDAEMON is True. If that
    fails or if USE_KEYDAEMON is False, directly generates a key.
  <Returns>
    A tuple in the format (pubkeystr, privkeystr).
  """
  
  if USE_KEYDAEMON:
    try:
      return _generate_keypair_from_key_daemon()
    except:
      log.critical("Unable to generate key from key daemon, falling back to " + 
                   "manual key generation. This may be very slow. The error " +
                   " from the key daemon was: " + traceback.format_exc())

  return _generate_keypair_directly()





@log_function_call_without_return
def _generate_keypair_directly():
  
  (pubkeydict, privkeydict) = rsa_gen_pubpriv_keys(MANUAL_GENERATION_BITSIZE)

  pubkeystring = rsa_publickey_to_string(pubkeydict)
  privkeystring = rsa_privatekey_to_string(privkeydict)
  
  return (pubkeystring, privkeystring)





@log_function_call_without_return
def _generate_keypair_from_key_daemon():
  
  # TODO: implement obtaining keys from the key daemon.
  raise NotImplementedError

