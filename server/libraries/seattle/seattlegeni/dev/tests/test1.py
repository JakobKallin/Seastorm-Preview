# Modules to make available for convenience so the names are available in the
# ipython shell. Just a lazy way to not have to execute these lines individually
# in a new shell.
from seattlegeni.common.api import maindb
from seattlegeni.common.exceptions import *
from seattlegeni.website.control import interface

import random

def testfailed(reason):
  raise Exception("Test failed: " + reason)

username = 'testuser' + str(random.randint(0, 1000000))

# Create a user.
geniuser = interface.register_user(username, 'mypass', 'joe@example.com', 'myaffiliation')

# Get the user.
geniuser = interface.get_user_with_password(username, 'mypass')

# Make sure the private key was created because we didn't provide a pubkey when
# creating the user.
privkey = interface.get_private_key(geniuser)

if privkey is None:
  testfailed("private key wasn't created")

# Delete the private key and make sure it gets deleted.
interface.delete_private_key(geniuser)

privkey = interface.get_private_key(geniuser)
if privkey is not None:
  testfailed("private key wasn't deleted: " + str(privkey))

# Make sure they don't have any donations initially.
donations = interface.get_donations(geniuser)
if len(donations) > 0:
  testfailed("The user shouldn't have any donations.")

INITIAL_DONATION_COUNT = 6

# Create a few nodes and donations by this user.
for i in range(INITIAL_DONATION_COUNT):
  node_identifier = 'testnode' + username + str(i)
  extra_vessel_name = 'v2'
  ip = '127.0.' + str(i) + '.0'
  node = maindb.create_node(node_identifier, ip, 1234, '0.1a', True, 'the owner pubkey', extra_vessel_name)
  maindb.create_donation(node, geniuser, 'some resource description text')
  # Create the vessels on these nodes.
  name = 'testvessel' + username + str(i)
  vessel = maindb.create_vessel(node, name)
  # Set the vessel ports.
  ports = range(1000, 1010)
  ports.append(geniuser.usable_vessel_port)
  maindb.set_vessel_ports(vessel, ports)

donations = interface.get_donations(geniuser)
if len(donations) != INITIAL_DONATION_COUNT:
  testfailed("The user's donation count doesn't equal their number of donations.")

# Make sure they don't have any acquired vessels initially.
acquired_vessels = interface.get_acquired_vessels(geniuser)
if len(acquired_vessels) > 0:
  testfailed("The user shouldn't have any acquired vessels.")

# Try to acquire vessels when there are none that match what they request.
# At this point, we expect the user to have 70 vessel credits (default 10
# plus 6 * 10 for donations).
try:
  interface.acquire_vessels(geniuser, 50, 'wan')
except UnableToAcquireResourcesError: 
  pass # This is what we expected.
else:
  testfailed("Didn't throw expected UnableToAcquireResourcesError")

# Try to acquire more vessels than the user should be allowed to.
try:
  interface.acquire_vessels(geniuser, 100, 'wan')
except InsufficientUserResourcesError:
  pass # This is what we expected.
else:
  testfailed("Didn't throw expected InsufficientUserResourcesError")

# Acquire INITIAL_DONATION_COUNT wan vessels. There should be at least this
# many because we just made them.
acquired_vessels = interface.acquire_vessels(geniuser, INITIAL_DONATION_COUNT, 'wan')

if len(acquired_vessels) != INITIAL_DONATION_COUNT:
  testfailed("Didn't acquire the number of vessels expected.")

# Release one vessel.
vessel_to_release = acquired_vessels[0]
interface.release_vessels(geniuser, [vessel_to_release])

acquired_vessels = interface.get_acquired_vessels(geniuser)
if len(acquired_vessels) != INITIAL_DONATION_COUNT - 1:
  testfailed("Wrong number of acquired vessels after releasing one.")
  
# Try to release the same one again.
try:
  interface.release_vessels(geniuser, [vessel_to_release])
except InvalidRequestError:
  pass # This is what we expected.
else:
  testfailed("Didn't throw expected InvalidRequestError")

# Release the rest of the user's vessels.
interface.release_all_vessels(geniuser)

acquired_vessels = interface.get_acquired_vessels(geniuser)
if len(acquired_vessels) != 0:
  testfailed("Wrong number of acquired vessels after releasing all vessels.")


