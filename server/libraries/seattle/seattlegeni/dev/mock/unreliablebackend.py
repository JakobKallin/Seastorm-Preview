"""
Currently just replaces the backend.acquire_vessel function to make it claim
to fail half of the time. 
"""

import random

from seattlegeni.common.api import backend

from seattlegeni.common.exceptions import UnableToAcquireResourcesError

print "Mocking: seattlegeni.common.api.backend.acquire_vessel"

def mock_acquire_vessel(geniuser, vessel):
  if random.randint(0, 1) == 1:
    raise UnableToAcquireResourcesError

backend.acquire_vessel = mock_acquire_vessel
