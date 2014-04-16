"""
<Program Name>
  stop_seattle_affix.py

<Purpose>
  This is a very simple script that uses the Seattle
  advertise service to disable Affixes for Seattle 
  nodemanager and defines what Affixes they should
  use.
"""

from repyportability import *
_context = locals()
add_dy_support(_context)

dy_import_module_symbols("advertise.repy")

affix_stack_key = "SeattleAffixStack"
enable_affix_key = "EnableSeattleAffix"

try:
    advertise_announce(affix_stack_key, "(NoopShim)", 600)
except AdvertiseError, e:
    print "Advertise error: " + str(e)

# Check what the flag is set to.
try:
    lookup_string = advertise_lookup(affix_stack_key)
except (AdvertiseError, TimeoutError):
    print "Unable to lookup key '%s' due to advertise error." % affix_stack_key
else:
    print "Current lookup string is: " + str(lookup_string)

# Disable Affixes for Seattle.
try:
    advertise_announce(enable_affix_key, "False", 600)
except AdvertiseError, e:
    print "Advertise error: " + str(e)

# Check what the Affix flag is set to.
try:
    lookup_string = advertise_lookup(enable_affix_key)
except (AdvertiseError, TimeoutError):
    print "Unable to lookup key '%s' due to advertise error." % enable_affix_key
else:    
    print "EnableSeattleAffix flag set to: " + str(lookup_string)

