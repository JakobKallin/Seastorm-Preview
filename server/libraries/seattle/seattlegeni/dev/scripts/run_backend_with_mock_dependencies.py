#!/usr/bin/env python

from seattlegeni.backend import backend_daemon
from seattlegeni.common.api import keydb
from seattlegeni.common.api import nodemanager

from seattlegeni.common.util.decorators import log_function_call

@log_function_call
def _mock_do_signed_call(nodehandle, *callargs):
  pass
nodemanager._do_signed_call = _mock_do_signed_call

@log_function_call
def mock_get_private_key(pubkey):
  return 'Mock private key'
keydb.get_private_key = mock_get_private_key

@log_function_call
def mock_set_private_key(pubkey, privkey, keydescription):
  pass
keydb.set_private_key = mock_set_private_key

# Start the backend.
backend_daemon.main()

