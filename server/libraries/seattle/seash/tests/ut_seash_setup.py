"""
Makes sure that vessels on the nodemanager are accessible before continuing with
the unit tests.  This is essential so that the first few unit tests don't fail 
because the node manager isn't ready yet.

Also disables all modules so that individual module tests can assume a clean
module system before running.
"""

# Needed so that the built-in type function is restored to the python
# abc library
import seash_dictionary

# Disable all modules.
# We pass in an empty dict because we only care that the .disabled file gets 
# created
import seash_modules
for module in seash_modules.get_enabled_modules():
  # The modules module must always be enabled.  Otherwise, we have no way of
  # enabling/disabling modules through the command loop.
  if module == 'modules':
    continue
  seash_modules.disable({}, module)

from repyportability import *
add_dy_support(locals())

dy_import_module_symbols('rsa.repy')
dy_import_module_symbols('advertise.repy')

for guestnum in xrange(4):
  guestkey = rsa_file_to_publickey('guest'+str(guestnum)+'.publickey')
  while not advertise_lookup(guestkey, graceperiod=1):
    sleep(2)