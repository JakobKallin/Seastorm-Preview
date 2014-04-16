"""
Test that the geoip module functions correctly.

"""
import os
import seash
import sys

# We need the modules module
import seash_modules
import seash_dictionary
#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


commands = [
  'enable geoip',
  'disable geoip',
  'enable geoip',
  'loadkeys guest0',
  'as guest0',
  'browse',
  'on %1',
  'show location',
  'show coordinates'
]

# Allow the geoip module to be disabled when done, 
# even if exceptions occur
try:
  seash.command_loop(commands)
except Exception, e:
  print>>sys.stderr, str(e)

# Make sure the geoip module is disabled after this run.
# This is to ensure that other modules' tests are not affected by this module.
seash.command_loop(['disable geoip'])