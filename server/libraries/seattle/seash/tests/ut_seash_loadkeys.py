"""
Loads a series of keys and make sures seash recognizes them correctly.
"""
import seash
import sys
from repyportability import add_dy_support
add_dy_support(locals())
dy_import_module_symbols('rsa.repy')


orig_stdout = sys.stdout

# Prepare the expected results.

# This list of tuples dictates whether the specified guest has its 
# public/private keys loaded.
# Each tuple represents: (guestname, publickey, privatekey)
guest_has_keys = [('guest2', True, True),
                  ('guest0', True, False),
                  ('guest1', False, True)]

sys.stdout = open("loadkeys_test_results.txt", "w")

# show keys
# Guestname Publickey/None Privatekey/None
# None is printed only if that key isn't loaded.
# e.g.:
# guest0 {'e': 65537L, 'n': 899L} {'q': 31L, 'p': 29L, 'd': 593L}
# guest1 None {'q': 31L, 'p': 29L, 'd': 593L}
# guest2 {'e': 65537L, 'n': 899L} None

for (guest, haspublic, hasprivate) in guest_has_keys:
  print guest,
  print rsa_file_to_publickey(guest + ".publickey") if haspublic else None,
  print rsa_file_to_privatekey(guest + ".privatekey") if hasprivate else None

# show identities
# Same as show keys, except:
#   Keys are replaced by the tokens "PUB" and "PRIV"
#   If a key is not found, it is simply not printed
for (guest, haspublic, hasprivate) in guest_has_keys:
  print guest, 
  if haspublic:
    print "PUB", 
  if hasprivate:
    print "PRIV",
  print

sys.stdout.close()

# Begin testing
sys.stdout = open("test_results.txt", "w")
command_list = [
  'loadpub guest0',
  'loadpriv guest1', 
  'loadkeys guest2', 
  'show keys', 
  'show identities'
  ]

seash.command_loop(command_list)

sys.stdout.close()


# Compare the results to make sure key values and identities as recognized
# by seash are identical.
sys.stdout = orig_stdout

test_results = open("test_results.txt", "r")
wanted_results = open("loadkeys_test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i].startswith(actual[i]):
    print "Line " + str(i) + " of test results are not consistent with expected results: loadkeys_test_results.txt"

test_results.close()
wanted_results.close()

