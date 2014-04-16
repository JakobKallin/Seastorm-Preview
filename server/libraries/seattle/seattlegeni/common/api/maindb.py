"""
<Program>
  maindb.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is the API that should be used to interact with the Main Database.
  Functions in this module are the only way that other code should interact
  with the Main Database.
   
  Note: it is yet to be determined how strict the rule of "the only way to
  interact with the Main Database" should be. It is likely that functions
  in this module will return values that will, for example, lazily load
  data from the database. The point is to hide as much of the underlying
  database interaction from other code. It is definitely the case that
  no code outside this module should be modifying the database.
  
  We try to keep all manual transaction management in seattlegeni to within
  this module. The general idea is that the default behavior of django is
  what we want in most places (to commit any time data-altering functions
  are called, such as .save() or .delete()). However, in a few cases we
  want multiple data-altering functions to be committed atomically, so we
  use @transaction.commit_manually.
"""

# It is a bit confusing to just import datetime because then you have to use
# things like 'datetime.datetime.now()'. So, import the parts we need.
from datetime import datetime
from datetime import timedelta

import django.contrib.auth.models
import django.core.exceptions
import django.db

from django.db import transaction

import random

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import log

from seattlegeni.common.util.decorators import log_function_call
from seattlegeni.common.util.decorators import log_function_call_and_only_first_argument

from seattlegeni.common.util.assertions import *

from seattlegeni.website import settings

from seattlegeni.website.control.models import Donation
from seattlegeni.website.control.models import GeniUser
from seattlegeni.website.control.models import Node
from seattlegeni.website.control.models import Vessel
from seattlegeni.website.control.models import VesselPort
from seattlegeni.website.control.models import VesselUserAccessMap
from seattlegeni.website.control.models import ActionLogEvent
from seattlegeni.website.control.models import ActionLogVesselDetails





# The number of free vessel credits each user gets regardless of donations.
# This is the value set for newly-created users. Changing this value only
# affects new user accounts, not existing ones.
DEFAULT_FREE_VESSEL_CREDITS = 10

# A user gets 10 vessel credits for every donation they make.
VESSEL_CREDITS_FOR_DONATIONS_MULTIPLIER = 10

# Port from this range will be randomly selected as the usable_vessel_port for
# new users. Remember that range(x, y) is x inclusive, y exclusive. 
ALLOWED_USER_PORTS = range(63100, 63180)

# Number of ascii characters in generated API keys.
API_KEY_LENGTH = 32

# When initially acquired, this is the amount of time from now until a vessel
# will expire.
# This must be a datetime.timedelta object.
DEFAULT_VESSEL_EXPIRATION_TIMEDELTA = timedelta(hours=4)

# When a vessel is renewed, this is the amount of time from now until a vessel
# will expire.
MAXIMUM_VESSEL_EXPIRATION_TIMEDELTA = timedelta(days=7)

# When calls to get_available_*_vessels() are made, we try to return more
# vessels than were requested so that there will be extras in case some
# can't be acquired. The number we try to return is the number requested times
# the multiplier plus the adder. This gives the chance for half of the nodes
# to be unavailable but the adder makes sure small numbers of requested
# vessels (e.g. 1) won't fail due to really bad luck with the returned vessels.
GET_AVAILABLE_VESSELS_MULTIPLIER = 2
GET_AVAILABLE_VESSELS_ADDER = 10

# The maximum number of lists of same-subnet vessels to return from a call to
# get_available_lan_vessels_by_subnet(). This is useful because if, for example,
# the user requested one lan vessel, we might return (not to the user) a list that
# includes a list of vessels for every possible subnet covered by active nodes.
# That wouldn't be the end of the world, but it seems a bit excessive if we have
# nodes on thousands of subnets.
GET_AVAILABLE_LAN_VESSELS_MAX_SUBNETS = 10

# The string that is the prefix to all NAT strings in node last_known_ip fields.
NAT_STRING_PREFIX = "NAT$"





@log_function_call
def init_maindb():
  """
  <Purpose>
    Initializes the database in a way that makes database transaction commits
    from other sources immediately visible. Must be called after creating
    any database connection.
    
    If you're using the maindb in long-running non-website code, you should
    either call this function on a regular basis (even if new database
    connections haven't been made) or copy the bit of code here that does the
    django.db.reset_queries() call to your own code. Otherwise, your memory
    usage will grow due to query logging when DEBUG is True.
  <Arguments>
    None.
  <Exceptions>
    It is possible for a Django / Database error to be thrown (which is fatal).
  <Side Effects>
    This function makes it so that we see any transactions commits made by
    other database clients even within a single transaction on the side
    of the script that calls this function.
    This is done by changing the transaction isolation level of InnoDB from the
    default of "repeatable read" to instead be "read committed". For more info, see:
    http://dev.mysql.com/doc/refman/5.4/en/innodb-consistent-read.html
    http://dev.mysql.com/doc/refman/5.4/en/set-transaction.html
  <Returns>
    None.
  """
  if settings.DATABASE_ENGINE is "mysql":
    django.db.connection.cursor().execute('set transaction isolation level read committed')
  else:
    log.error("init_maindb() called when not using mysql. This is only OK when developing.")

  # We shouldn't be running in production with settings.DEBUG = True. Just in
  # case, though, tell django to reset its list of saved queries. On the
  # website, init_maindb() will get called with each web request so we'll be
  # resetting the queries at the beginning of each request.
  # See http://docs.djangoproject.com/en/dev/faq/models/#why-is-django-leaking-memory
  # for more info.
  if settings.DEBUG:
    log.debug("Resetting django query log because settings.DEBUG is True.")
    log.error("Reminder: settings.DEBUG is True. Don't run in production like this!")
    django.db.reset_queries()



@transaction.commit_manually
@log_function_call_and_only_first_argument
def create_user(username, password, email, affiliation, user_pubkey, user_privkey, donor_pubkey):
  """
  <Purpose>
    Create a new seattlegeni user in the database. This user will be able to
    login to website, use the seattlegeni xmlrpc api, acquire vessels, etc.
    
    A 'user' lock should be held on the specified username before calling this
    function. The code calling this function should have already checked to
    see whether a user by this username exists (and did so while holding the
    lock on that username).
  
    The code calling this function is responsible for first storing the
    corresponding private key of donor_pubkey in the keydb. In the case of the
    website calling this function, the website will make a call to the backend
    to request a new key and that will take care of storing the donor private
    key in the keydb.
    
  <Arguments>
    username
      The username of the user to be created.
    password
      The user's password.
    email
      The user's email address.
    affiliation
      The affiliation text provided by the user.
    user_pubkey
      A string of the user's public key.
    user_privkey
      A string of the user's private key or None. This would be None if the
      user has provided their own public key rather than had us generate
      a keypair for them.
    donor_pubkey
      A string of the user's donor key. This is a key the user never sees (and
      probably never knows exists).  
      
    <Exceptions>
      None
      
    <Side Effects>
      Creates a user record in the django user table and a user record in the
      seattlegeni geniuser table, the two of which have a one-to-one mapping.
      Does not change the database if creation of either record fails.
      
    <Returns>
      A GeniUser object of the newly created user.
  """
  assert_str(username)
  assert_str(password)
  assert_str(email)
  assert_str(affiliation)
  assert_str(user_pubkey)
  assert_str_or_none(user_privkey)
  assert_str(donor_pubkey)
  
  # We're committing manually to make sure the multiple database writes are
  # atomic. (That is, regenerate_api_key() will do a database write.)
  try:
    # Generate a random port for the user's usable vessel port.
    port = random.sample(ALLOWED_USER_PORTS, 1)[0]
  
    # Create the GeniUser (this is actually records in two different tables
    # underneath because of model inheretance, but django hides that from us).
    geniuser = GeniUser(username=username, password='', email=email,
                        affiliation=affiliation, user_pubkey=user_pubkey,
                        user_privkey=user_privkey, donor_pubkey=donor_pubkey,
                        usable_vessel_port=port,
                        free_vessel_credits=DEFAULT_FREE_VESSEL_CREDITS)
    # Set the password using this function so that it gets hashed by django.
    geniuser.set_password(password)
    geniuser.save()
  
    regenerate_api_key(geniuser)
    
  except:
    transaction.rollback()
    raise
  
  else:
    transaction.commit()

  return geniuser





@log_function_call
def regenerate_api_key(geniuser):
  """
  <Purpose>
    Set a new, randomly generated api key for a user.
  <Arguments>
    geniuser
      The GeniUser object of the user whose api key is to be regenerated.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with a new,
    randomly-generated api key.
  <Returns>
    The new api key that has been set for the user.
  """
  assert_geniuser(geniuser)
  
  # Create a set of potential characters for the api key that includes the
  # numbers 0-9 and the uppercase charactesr A-Z, excluding the letter 'O'
  # because it looks too much like zero.
  population = []
  population.extend(range(ord('0'), ord('9') + 1))
  population.extend(range(ord('A'), ord('Z') + 1))
  population.remove(ord('O'))
  
  api_key = ""
  for character in random.sample(population, API_KEY_LENGTH):
    api_key += chr(character)
    
  geniuser.api_key = api_key
  geniuser.save()

  return api_key





@log_function_call
def set_user_keys(geniuser, pubkey, privkey):
  """
  <Purpose>
    Sets the public/private user keys for the geniuser.
  <Arguments>
    geniuser
      The GeniUser object of the user whose keys are to be changed.
    pubkey
      The public key string of the public key to be set for the user.
    privkey
      The private key string of the private key to be set for the user. This
      can be None if no private key should be stored in the database.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with the
    provided keys.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  geniuser.user_pubkey = pubkey
  geniuser.user_privkey = privkey
  geniuser.save()





@log_function_call
def set_user_email(geniuser, new_email):
  """
  <Purpose>
    Sets the email for the geniuser.
  <Arguments>
    geniuser
      The GeniUser object of the user whose email is to be changed.
    new_email  
      The new email value.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with the
    provided email.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  geniuser.email = new_email
  geniuser.save()





@log_function_call
def set_user_affiliation(geniuser, new_affiliation):
  """
  <Purpose>
    Sets the affiliation for the geniuser.
  <Arguments>
    geniuser
      The GeniUser object of the user whose affiliation is to be changed.
    new_affiliation  
      The new affiliation value.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with the
    provided affiliation.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  geniuser.affiliation = new_affiliation
  geniuser.save()





@log_function_call
def set_user_port(geniuser, new_port): # currently not in use 
  """
  <Purpose>
    Sets the port for the geniuser.
  <Arguments>
    geniuser
      The GeniUser object of the user whose port is to be changed.
    new_port  
      The new port value.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with the
    provided port.
  <Returns>
    None
  """
  # if new_port in ALLOWED_USER_PORTS:
  assert_geniuser(geniuser)
  
  geniuser.usable_vessel_port = new_port
  geniuser.save()





@log_function_call_and_only_first_argument
def set_user_password(geniuser, new_password):
  """
  <Purpose>
    Sets the password for the geniuser.
  <Arguments>
    geniuser
      The GeniUser object of the user whose password is to be changed.
    new_password  
      The new password value.
  <Exceptions>
    None
  <Side Effects>
    Updates the database as well as the geniuser object passed in with the
    provided password.
  <Returns>
    None
  """
  assert_geniuser(geniuser)

  # Set the password using this function so that it gets hashed by django.
  geniuser.set_password(new_password)
  geniuser.save()





@log_function_call
def create_node(node_identifier, last_known_ip, last_known_port, last_known_version, is_active, owner_pubkey, extra_vessel_name):
  """
  <Purpose>
    Create a new node record in the database. A node lock should be held before
    calling this function.
  <Arguments>
    node_identifier
      The identifier of the node to be created (there must be any existing
      nodes with this identifier).
    last_known_ip
      The last known ip address (a string) that this node's nodemanager was
      running on.
    last_known_port
      The last known port (an int) that this node's nodemanager was running on.
    last_known_version
      The last known version of Seattle (a string) that this node was running.
    is_active
      Whether this node is considered to be up.
    owner_pubkey
      The owner public key (a string) that SeattleGeni uses for this node. The
      corresponding private key must be stored in the keydb.
    extra_vessel_name
      The name of the 'extra vessel' on this node (a string).
  <Exceptions>
    None
  <Side Effects>
    A node record is created in the database.
  <Returns>
    The Node object of the created node.
  """
  assert_str(node_identifier)
  assert_str(last_known_ip)
  assert_int(last_known_port)
  assert_str(last_known_version)
  assert_bool(is_active)
  assert_str(owner_pubkey)
  assert_str(extra_vessel_name)
  
  # Make sure there is not already a node with this node identifier.
  try:
    get_node(node_identifier)
    raise ProgrammerError("A node with this identifier already exists: " + node_identifier)
  except DoesNotExistError:
    pass
  
  # Create the Node.
  node = Node(node_identifier=node_identifier, last_known_ip=last_known_ip,
              last_known_port=last_known_port, last_known_version=last_known_version,
              is_active=is_active, owner_pubkey=owner_pubkey,
              extra_vessel_name=extra_vessel_name, is_broken=False)
  node.save()

  return node





def get_allowed_user_ports():
  """
  <Purpose>
    Gets the allowed user ports defined globally in this file.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The allowed user ports which are a list.
  """
  return ALLOWED_USER_PORTS





@log_function_call
def create_donation(node, donor, resource_description_text):
  """
  <Purpose>
    Create a new donation record in the database. A node lock and a user lock
    should be held before calling this function.
  <Arguments>
    node
      The Node object of the node that the donation was made from.
    donor
      The GeniUser object of the user that made the donation.
    resource_description_text
      A description of the donated resources (in the format of other resource
      descriptions used in Seattle).
  <Exceptions>
    None
  <Side Effects>
    A donation record is created in the database.
  <Returns>
    The Donation object of the created donation.
  """
  assert_node(node)
  assert_geniuser(donor)
  assert_str(resource_description_text)
  
  # Create the Donation.
  donation = Donation(node=node, donor=donor,
                      resource_description_text=resource_description_text)
  donation.save()

  return donation





@log_function_call
def create_vessel(node, vesselname):
  """
  <Purpose>
    Create a new vessel record in the database. A node lock should be held
    before calling this function.
  <Arguments>
    node
      The Node object of the node that the vessel exists on.
    vesselname
      The name of the vessel for the vessel record to be created.
  <Exceptions>
    None
  <Side Effects>
    A vessel record is created in the database.
  <Returns>
    The Vessel object of the created vessel.
  """
  assert_node(node)
  assert_str(vesselname)
  
  # Create the Vessel.
  vessel = Vessel(node=node, name=vesselname, acquired_by_user=None,
                  date_acquired=None, date_expires=None, is_dirty=False,
                  user_keys_in_sync=True)
  vessel.save()
  
  return vessel





@transaction.commit_manually
@log_function_call
def set_vessel_ports(vessel, port_list):
  """
  <Purpose>
    Change the list of ports the database considers associated with a vessel.
    A node lock should be held before calling this function.
  <Arguments>
    vessel
      The Vessel object whose list of ports is to be changed.
    port_list
      The list of port numbers (int's or long's) that are the complete list
      of ports for this vessel.
  <Exceptions>
    None
  <Side Effects>
    The database indicates that the ports in port_list (and only those ports)
    are the ports for the vessel. 
  <Returns>
    None
  """
  assert_vessel(vessel)
  assert_list(port_list)
  for port in port_list:
    assert_int(port)

  # We're committing manually to make sure the multiple database writes are
  # atomic.
  try:
    # Delete all existing VesselPort records for this vessel.
    VesselPort.objects.filter(vessel=vessel).delete()
    
    # Create a VesselPort record for each port in port_list.
    for port in port_list:
      vesselport = VesselPort(vessel=vessel, port=port)
      vesselport.save()

  except:
    transaction.rollback()
    raise
  
  else:
    transaction.commit()





@log_function_call
def get_users_with_access_to_vessel(vessel):
  """
  <Purpose>
    Determine which users have access to a vessel according to the database.
  <Arguments>
    vessel
      The Vessel object whose user access is info is wanted.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of GeniUser objects of the users who have access to the vessel.
  """
  assert_vessel(vessel)

  user_list = []

  for vmap in VesselUserAccessMap.objects.filter(vessel=vessel):
    user_list.append(vmap.user)

  return user_list





@log_function_call
def get_vessels_accessible_by_user(geniuser):
  """
  <Purpose>
    Determine which vessels the database indicates the user has access to.
  <Arguments>
    geniuser
      The GeniUser object of the user whose vessel access info is wanted.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects of the vessels the user has access to.
  """
  assert_geniuser(geniuser)
  
  vessel_list = []
  
  for vmap in VesselUserAccessMap.objects.filter(user=geniuser):
    vessel_list.append(vmap.vessel)

  return vessel_list





@log_function_call
def add_vessel_access_user(vessel, geniuser):
  """
  <Purpose>
    Indicate in the database that a user has access to a vessel. A node lock
    and a user lock should be held before calling this function.
  <Arguments>
    vessel
      The Vessel object that the user is being given access to.
    geniuser
      The GeniUser object of the user that being access to the vessel.
  <Exceptions>
    None
  <Side Effects>
    The database indicates that the user has access to the vessel.
  <Returns>
    None
  """
  assert_vessel(vessel)
  assert_geniuser(geniuser)

  # If the user already has access, don't throw an exception, just consider
  # the request done.
  mapqueryset = VesselUserAccessMap.objects.filter(vessel=vessel, user=geniuser)
  if mapqueryset.count() == 1:
    return
  
  # Create a VesselUserAccessMap record.
  maprecord = VesselUserAccessMap(vessel=vessel, user=geniuser)
  maprecord.save()
  
  
  
  
  
@log_function_call
def remove_vessel_access_user(vessel, geniuser):
  """
  <Purpose>
    Indicate in the database that a user no longer has access to a vessel. A
    node lock and a user lock should be held before calling this function.
  <Arguments>
    vessel
      The Vessel object that the user is having access removed from.
    geniuser
      The GeniUser object of the user that is having access removed.
  <Exceptions>
    None
  <Side Effects>
    The database no longer indicates that the user has access to the vessel.
  <Returns>
    None
  """
  assert_vessel(vessel)
  assert_geniuser(geniuser)

  # Delete any map records for this user/vessel.
  VesselUserAccessMap.objects.filter(vessel=vessel, user=geniuser).delete()





@log_function_call
def _remove_all_user_access_to_vessel(vessel):
  """
  <Purpose>
    Indicate in the database that no user has access to the vessel.
  <Arguments>
    vessel
      The Vessel object to have all user access removed.
  <Exceptions>
    None
  <Side Effects>
    The database no longer indicates that any user has access to the vessel.
  <Returns>
    None
  """
  assert_vessel(vessel)

  # Delete any map records for this user/vessel.
  VesselUserAccessMap.objects.filter(vessel=vessel).delete()





@log_function_call
def get_user(username, allow_inactive=False):
  """
  <Purpose>
    Retrieve the user that a has the given username.
  <Arguments>
    username
      The username of the user to be retrieved.
    allow_inactive
      If True, don't raise an exception if the account is inactive (which
      means probably banned for being a bad citizen).
  <Exceptions>
    DoesNotExistError
      If there is no user with the given username.
  <Side Effects>
    None
  <Returns>
    The GeniUser object of the user.
  """
  assert_str(username)
  
  try:
    geniuser = GeniUser.objects.get(username=username)
    if not geniuser.is_active and not allow_inactive:
      # They've probably been banned. We could completely lie, but if this is
      # really a banned account then they probably know they've been banned.
      # If it's not someone who was up to no good, then they should be
      # encouraged to contact us (at least, if they get to see this message).
      raise DoesNotExistError("Account must be activated. Please contact support.")
    
  except django.core.exceptions.ObjectDoesNotExist:
    # Intentionally vague message to prevent a security problem if this ever
    # gets displayed on the frontend (needs to be the same message as the
    # password/apikey authentication failure messages).
    raise DoesNotExistError("No such user.")
    
  except django.core.exceptions.MultipleObjectsReturned:
    raise InternalError("Multiple records returned when looking up a user by username.")

  return geniuser





@log_function_call_and_only_first_argument
def get_user_with_password(username, password):
  """
  <Purpose>
    Retrieve the user that a has the given username and password.
  <Arguments>
    username
      The username of the user to be retrieved.
    password
      The password of the user to be retrieved.
  <Exceptions>
    DoesNotExistError
      If there is no user with the given username and password.
  <Side Effects>
    None
  <Returns>
    The GeniUser object of the user.
  """
  assert_str(username)
  assert_str(password)
  
  # Throws a DoesNotExistError if there is no such user.
  geniuser = get_user(username)

  if not django.contrib.auth.models.check_password(password, geniuser.password):
    # Intentionally vague message to prevent a security problem if this ever
    # gets displayed on the frontend.
    raise DoesNotExistError("No such user.")
  
  return geniuser





@log_function_call_and_only_first_argument
def get_user_with_api_key(username, api_key):
  """
  <Purpose>
    Retrieve the user that a has the given username and api_key.
  <Arguments>
    username
      The username of the user to be retrieved.
    api_key
      The api_key of the user to be retrieved.
  <Exceptions>
    DoesNotExistError
      If there is no user with the given username and api_key.
  <Side Effects>
    None
  <Returns>
    The GeniUser object of the user.
  """
  assert_str(username)
  assert_str(api_key)
  
  # Throws a DoesNotExistError if there is no such user.
  geniuser = get_user(username)

  if not geniuser.api_key == api_key:
    # Intentionally vague message to prevent a security problem if this ever
    # gets displayed on the frontend.
    raise DoesNotExistError("No such user.")
  
  return geniuser




@log_function_call
def get_donor(donor_pubkey):
  """
  <Purpose>
    Retrieve the user that has the donor_pubkey,
  <Arguments>
    donor_pubkey
      The key that is the user's donor key.
  <Exceptions>
    DoesNotExistError
      If there is no user with the given donor_pubkey.
  <Side Effects>
    None
  <Returns>
    The GeniUser object of the user who is the donor.
  """
  assert_str(donor_pubkey)
  
  try:
    geniuser = GeniUser.objects.get(donor_pubkey=donor_pubkey)
    
  except django.core.exceptions.ObjectDoesNotExist:
    raise DoesNotExistError("No user exists with the specified donor_pubkey.")
    
  except django.core.exceptions.MultipleObjectsReturned:
    raise InternalError("Multiple records returned when looking up a user by donor_pubkey.")

  return geniuser





@log_function_call
def get_donations_from_node(node):
  """
  <Purpose>
    Retrieve the donation records of the donations from a node.
  <Arguments>
    node
      The Node object of the node from which the donations were made.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Donation objects.
  """
  assert_node(node)
  
  return list(Donation.objects.filter(node=node))





@log_function_call
def get_node_identifier_from_vessel(vessel):
  """
  <Purpose>
    Determine the node id of the node a vessel is on.
  <Arguments>
    vessel
      The Vessel object of the vessel whose node's nodeid will be retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The node id (a string).
  """
  assert_vessel(vessel)
  
  return vessel.node.node_identifier





@log_function_call
def delete_user_private_key(geniuser):
  """
  <Purpose>
    Delete the user's private user key. A user lock should be held before
    calling this function.
  <Arguments>
    geniuser
      The user whose private key is to be deleted.
  <Exceptions>
    None
  <Side Effects>
    The user's private key has been removed from the database.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  
  geniuser.user_privkey = None
  geniuser.save()





@log_function_call
def get_donations_by_user(geniuser, include_inactive_and_broken=False):
  """
  <Purpose>
    Retrieve a list of all donations made by a user. By default, only includes
    donations from nodes that are active and not broken.
  <Arguments>
    geniuser
      The user whose donations are to be retrieved.
    include_inactive_and_broken
      Whether to include donations by the user that are from nodes which are
      inactive and/or broken. Default is False.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Donation objects.
  """
  assert_geniuser(geniuser)
  
  queryset = Donation.objects.filter(donor=geniuser)
  if not include_inactive_and_broken:
    queryset = queryset.filter(node__is_active=True)
    queryset = queryset.filter(node__is_broken=False)
  
  # Let's return it as a list() rather than a django QuerySet.
  # Using list() causes the QuerySet to be converted to a list, which also
  # means the query is executed (no lazy loading).
  return list(queryset)





@log_function_call
def get_node(node_identifier):
  """
  <Purpose>
    Retrieve a Node object that represents a specific node.
  <Arguments>
    node_identifier
      The identifier of the node to be retrieved.
  <Exceptions>
    DoesNotExistError
      If there is no node in the database with the provided identifier.
  <Side Effects>
    None
  <Returns>
    A Node object.
  """
  assert_str(node_identifier)

  try:
    node = Node.objects.get(node_identifier=node_identifier)
    
  except django.core.exceptions.ObjectDoesNotExist:
    raise DoesNotExistError("There is no node with the node identifier: " + str(node_identifier))
    
  except django.core.exceptions.MultipleObjectsReturned:
    raise InternalError("Multiple records returned when looking up a node by node identifier.")
  
  return node





@log_function_call
def set_node_owner_pubkey(node, ownerkeystring):
  """
  <Purpose>
    Change a node's owner key. A node lock should be held before calling this
    function.
  <Arguments>
    node
      The node object of the node whose owner key is to be modified.
    ownerkeystring
      The public key string to be set as the node's owner key.
  <Exceptions>
    None
  <Side Effects>
    The node's owner key is changed in the database and the node object passed
    in to the function reflects this.
  <Returns>
    None
  """
  assert_node(node)
  assert_str(ownerkeystring)
  
  node.owner_pubkey = ownerkeystring
  node.save()





@log_function_call
def record_node_communication_failure(node):
  """
  <Purpose>
    Let the database know that communication with a node has failed.
  <Arguments>
    node
      The node object of the node that couldn't be communicated with.
  <Exceptions>
    None
  <Side Effects>
    The node's is_active value is changed to False in the database and the
    node object passed in to the function reflects this.
  <Returns>
    None
  """
  assert_node(node)
  
  node.is_active = False
  node.save()





@log_function_call
def record_node_communication_success(node, version, ip, port):
  """
  <Purpose>
    Let the database know that communication with a node has succeeded and
    provide updated information about the node. This is really only intended
    to be used by transition scripts.
  <Arguments>
    node
      The Node object of the node that was successfully communicated with.
    version
      The version of seattle the node reports it is running.
    ip
      The ip address or NAT string the nodemanager is currently accessible at.
    port
      The port the nodemanager is currently accessible at.
  <Exceptions>
    None
  <Side Effects>
    The node's is_active value is changed to True in the database if it
    wasn't already, the date_last_contacted value is updated in the database
    to the current time, and the version, ip and port are updated. The node
    object passed in to the function reflects these changes.
  <Returns>
    None
  """
  assert_node(node)
  assert_str(version)
  assert_str(ip)
  assert_positive_int(port)
  
  node.last_known_version = version
  node.last_known_ip = ip
  node.last_known_port = port
  node.is_active = True
  node.date_last_contacted = datetime.now()
  node.save()





@log_function_call
def set_node_extra_vessel_name(node, extra_vessel_name):
  """
  <Purpose>
    Let the database know the name of the extra vessel on a node has changed.
    This is only intended to be used by transition scripts.
  <Arguments>
    node
      The Node object of the node that was successfully communicated with.
    extra_vessel_name
      The new name of the extra vessel on the node.
  <Exceptions>
    None
  <Side Effects>
    The node's extra_vessel_name value is changed in the database and the node
    object passed in to the function reflects the change.
  <Returns>
    None
  """
  assert_node(node)
  assert_str(extra_vessel_name)
  
  node.extra_vessel_name = extra_vessel_name
  node.save()





@log_function_call
def mark_node_as_active(node):
  """
  <Purpose>
    Let the database know that the node is active. This should only be used
    when a node moves from the canonical state to onepercent state. The
    onepercent-to-onepercent transition script will use the other method
    called record_node_communication_success(), instead.
  <Arguments>
    node
      The Node object of the node that is active.
  <Exceptions>
    None
  <Side Effects>
    The node's is_active value is changed to True in the database if it
    wasn't already. The node object passed to the function is correspondingly
    updated.
  <Returns>
    None
  """
  assert_node(node)
  
  node.is_active = True
  node.save()





@log_function_call
def mark_node_as_inactive(node):
  """
  <Purpose>
    Let the database know that the node is inactive. You shouldn't use this
    method if communication with a node fails. Instead, only use this if there
    is some other reason to mark the node as inactive (e.g. the node is up
    but the nodeid is wrong, indicating it's not seattle instance we expected).
  <Arguments>
    node
      The Node object of the node that is broken.
  <Exceptions>
    None
  <Side Effects>
    The node's is_broken value is changed to True in the database if it
    wasn't already. The node object passed to the function is correspondingly
    updated.
  <Returns>
    None
  """
  assert_node(node)
  
  node.is_active = False
  node.save()





@log_function_call
def mark_node_as_broken(node):
  """
  <Purpose>
    Let the database know that the node is broken (that is, what's one the node
    doesn't match our database). There currently isn't a corresponding function
    to mark the node as not broken because fixing a node will be a manual
    process.
  <Arguments>
    node
      The Node object of the node that is broken.
  <Exceptions>
    None
  <Side Effects>
    The node's is_broken value is changed to True in the database if it
    wasn't already. The node object passed to the function is correspondingly
    updated.
  <Returns>
    None
  """
  assert_node(node)
  
  node.is_broken = True
  node.save()





@log_function_call
def get_vessel(node_identifier, vesselname):
  """
  <Purpose>
    Retrieve a Vessel object that represents a specific vessel.
  <Arguments>
    node_identifier
      The identifier of the node that the vessel is on.
    vesselname
      The name of the vessel.
  <Exceptions>
    DoesNotExistError
      If there is no such vessel in the database (including if there is no node
      with the given identifier).
  <Side Effects>
    None
  <Returns>
    A Vessel object.
  """
  assert_str(node_identifier)
  assert_str(vesselname)

  try:
    vessel = Vessel.objects.get(node__node_identifier=node_identifier, name=vesselname)
    
  except django.core.exceptions.ObjectDoesNotExist:
    raise DoesNotExistError("There is no vessel with the node identifier: " + 
                            str(node_identifier) + " and vessel name: " + vesselname)
    
  except django.core.exceptions.MultipleObjectsReturned:
    raise InternalError("Multiple records returned when looking up a vessel by node identifier and vessel name.")
  
  return vessel





@log_function_call
def get_acquired_vessels(geniuser):
  """
  <Purpose>
    Retrieve a list of vessels that are acquired by a user.
  <Arguments>
    geniuser
      The GeniUser object of the user whose acquired vessels are to be
      retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects.
  """
  assert_geniuser(geniuser)
  
  # Let's return it as a list() rather than a django QuerySet.
  # Using list() causes the QuerySet to be converted to a list, which also
  # means the query is executed (no lazy loading).
  queryset = Vessel.objects.filter(acquired_by_user=geniuser)
  # We don't include expired vessels. That is, as far as what the user sees and
  # is considered having acquired, vessels expire immediately when their
  # expiration time arrives.
  queryset = queryset.exclude(date_expires__lte=datetime.now())
  return list(queryset)
  




def _get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(port):
  """
  Get a queryset of vessels that have a certain port and which are all
  available to be acquired. There is no restriction on whether these are
  vessels on nat nodes.
  """
  queryset = Vessel.objects.filter(acquired_by_user=None)
  # No dirty vessels or inactive nodes.
  queryset = queryset.exclude(is_dirty=True)
  queryset = queryset.exclude(node__is_active=False)
  queryset = queryset.exclude(node__is_broken=True)
  # Make sure we only get vessels with the user's assigned port.
  queryset = queryset.filter(vesselport__port__exact=port)
  # Randomize the vessels returned by the query.
  # Using order_by('?') is the QuerySet way of saying ORDER BY RAND().
  queryset = queryset.order_by('?')
  
  log.debug("There are " + str(queryset.count()) + " available NAT and non-NAT node vessels on port " + str(port))

  return queryset





def _get_queryset_of_all_available_vessels_for_a_port_exclude_nat_nodes(port):
  """
  Get a queryset of vessels that have a certain port and which are all
  available to be acquired. Excludes vessels on nat nodes.
  """
  queryset = _get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(port)
  
  queryset = queryset.exclude(node__last_known_ip__startswith=NAT_STRING_PREFIX)
  
  log.debug("There are " + str(queryset.count()) + " available non-NAT node vessels on port " + str(port))

  return queryset





def _get_queryset_of_all_available_vessels_for_a_port_only_nat_nodes(port):
  """
  Get a queryset of vessels that have a certain port and which are all
  available to be acquired. Only includes vessels on nat nodes.
  """
  queryset = _get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(port)
  
  queryset = queryset.filter(node__last_known_ip__startswith=NAT_STRING_PREFIX)
  
  log.debug("There are " + str(queryset.count()) + " available NAT node vessels on port " + str(port))

  return queryset





@log_function_call
def get_available_rand_vessels(geniuser, vesselcount):
  """
  <Purpose>
    Get a list of potential vessels that could satisfy the user's request for
    rand vessels.
  <Arguments>
    geniuser
      The user who is requesting vessels.
    veselcount
      The number of rand vessels the user has requested.
  <Exceptions>
     UnableToAcquireResourcesError
       If there are not enough resources in seattlegeni to fulfill the request.
  <Side Effects>
    None
  <Returns>
    A list of vessels that contains at least vesselcount vessels. These may be
    any type of vessels (some could be on nat nodes, some could be on the same
    subnet, etc.).
  """
  assert_geniuser(geniuser)
  assert_positive_int(vesselcount)
  
  # We return more vessels than were asked for. This gives some room for some
  # of the vessels to be inaccessible or already acquired by the time they are
  # attempted to be acquired by the client code.
  returnvesselcount = GET_AVAILABLE_VESSELS_MULTIPLIER * vesselcount + GET_AVAILABLE_VESSELS_ADDER
  
  allvesselsqueryset = _get_queryset_of_all_available_vessels_for_a_port_include_nat_nodes(geniuser.usable_vessel_port)
   
  if allvesselsqueryset.count() < vesselcount:
    message = "Requested " + str(vesselcount) + " rand vessels, but we only have " + str(allvesselsqueryset.count())
    message += " vessels with port " + str(geniuser.usable_vessel_port) + " available." 
    raise UnableToAcquireResourcesError(message)
  
  return list(allvesselsqueryset[:returnvesselcount])





@log_function_call
def get_available_nat_vessels(geniuser, vesselcount):
  """
  <Purpose>
    Get a list of potential vessels that could satisfy the user's request for
    nat vessels.
  <Arguments>
    geniuser
      The user who is requesting vessels.
    veselcount
      The number of nat vessels the user has requested.
  <Exceptions>
     UnableToAcquireResourcesError
       If there are not enough resources in seattlegeni to fulfill the request.
  <Side Effects>
    None
  <Returns>
    A list of vessels that contains at least vesselcount vessels. All vessels
    in the list will be nat vessels.
  """
  assert_geniuser(geniuser)
  assert_positive_int(vesselcount)
  
  # We return more vessels than were asked for. This gives some room for some
  # of the vessels to be inaccessible or already acquired by the time they are
  # attempted to be acquired by the client code.
  returnvesselcount = GET_AVAILABLE_VESSELS_MULTIPLIER * vesselcount + GET_AVAILABLE_VESSELS_ADDER
  
  natvesselsqueryset = _get_queryset_of_all_available_vessels_for_a_port_only_nat_nodes(geniuser.usable_vessel_port)
   
  if natvesselsqueryset.count() < vesselcount:
    #COMMENT this out when NAT acquistion feature is re-enabled  /* ADDED Aug 06, 2012 by GP */
    message = 'Acquiring NAT vessels is currently disabled. '
    #UNCOMMENT this when NAT acquistion feature is re-enabled
    #message = "Requested " + str(vesselcount) + " nat vessels, but we only have " + str(natvesselsqueryset.count())
    #message += " vessels with port " + str(geniuser.usable_vessel_port) + " available." 
    raise UnableToAcquireResourcesError(message)
  
  return list(natvesselsqueryset[:returnvesselcount])





@log_function_call
def get_available_wan_vessels(geniuser, vesselcount):
  """
  <Purpose>
    Get a list of potential vessels that could satisfy the user's request for
    wan vessels.
  <Arguments>
    geniuser
      The user who is requesting vessels.
    veselcount
      The number of wan vessels the user has requested.
  <Exceptions>
     UnableToAcquireResourcesError
       If there are not enough resources in seattlegeni to fulfill the request.
  <Side Effects>
    None
  <Returns>
    A list of vessels that contains at least vesselcount vessels. No two
    vessels in the list will have the same last octet of their IP address.
  """
  assert_geniuser(geniuser)
  assert_positive_int(vesselcount)
  
  # We return more vessels than were asked for. This gives some room for some
  # of the vessels to be inaccessible or already acquired by the time they are
  # attempted to be acquired by the client code.
  returnvesselcount = GET_AVAILABLE_VESSELS_MULTIPLIER * vesselcount + GET_AVAILABLE_VESSELS_ADDER
  
  vessellist = []
  includedsubnets = []
  
  nonnatvesselsqueryset = _get_queryset_of_all_available_vessels_for_a_port_exclude_nat_nodes(geniuser.usable_vessel_port)
   
  # Note: it would be more efficient to have the sql query return vessels
  # in unique subnets, but we would have to be very careful that the UNIQUE
  # wasn't being applied/interpreted "before" the RAND(). That is, we would
  # have to be careful that we weren't always getting the same node for a given
  # subnet. So, instead of worrying about the sql for that which wouldn't
  # be intuitive to do with the django ORM, let's just do that part manually.
  
  for possiblevessel in nonnatvesselsqueryset:
    
    subnet = possiblevessel.node.last_known_ip.rpartition('.')[0]
    if not subnet:
      log.error("The vessel " + str(possiblevessel) + " has an invalid last_known_ip")
      continue
    
    # For efficiency, includedsubnets should be a constant time lookup type.
    if subnet in includedsubnets:
      continue
    
    includedsubnets.append(subnet)
    vessellist.append(possiblevessel)
    
    if len(vessellist) == returnvesselcount:
      break 

  if len(vessellist) < vesselcount:
    message = "Requested " + str(vesselcount) + " wan vessels, but we only have vessels with port "
    message += str(geniuser.usable_vessel_port) + " available on " + str(len(includedsubnets)) + " subnets." 
    raise UnableToAcquireResourcesError(message)
  
  return vessellist





def _get_subnet_list():
  """
  Returns a randomly-ordered list of subnets that have at least one active
  non-nat node on the subnet.
  """
  
  # The commented out code only works on mysql but is more efficient. Leaving
  # it out for now as it's harder to test, as our tests run on sqlite.
  
  # Get a list of subnets that have at least vesselcount active nodes in the subnet.
  # This doesn't guarantee that there are available vessels for this user on
  # those nodes, but it's a start. We'll narrow it down further after we get
  # the list of possible subnets.
  #
  #  subnetsql = """SELECT COUNT(*) AS lansize,
  #                        SUBSTRING_INDEX(last_known_ip, '.', 3) AS subnet
  #                 FROM control_node
  #                 WHERE is_active = TRUE AND
  #                       is_broken = FALSE
  #                 GROUP BY subnet
  #                 HAVING lansize >= %s
  #                 ORDER BY RAND()""" % (vesselcount)
  #                 
  #  cursor = django.db.connection.cursor()
  #  cursor.execute(subnetsql)
  #  return cursor.fetchall()
  
  # Get a queryset of all active nodes.
  queryset = Node.objects.filter(is_active=True)
  queryset = queryset.filter(is_broken=False)
  queryset = queryset.exclude(last_known_ip__startswith=NAT_STRING_PREFIX)
  queryset = queryset.order_by('last_known_ip')

  previous_subnet = None
  subnetlist = []
  
  # Look through the queryset and build a list of unique subnets.
  for node in queryset:
    
    subnet = node.last_known_ip.rpartition('.')[0]
    
    if not subnet:
      log.error("The node " + str(node) + " has an invalid last_known_ip")
      continue
    
    if subnet != previous_subnet:
      subnetlist.append(subnet)
      previous_subnet = subnet
           
  # Randomize the order of the subnets.
  random.shuffle(subnetlist)
  
  return subnetlist
  




@log_function_call
def get_available_lan_vessels_by_subnet(geniuser, vesselcount):
  """
  <Purpose>
    Get a list of potential subnets (and a list of vessels in the subnet)
    that could satisfy the user's request for lan vessels.
  <Arguments>
    geniuser
      The user who is requesting vessels.
    veselcount
      The number of lan vessels the user has requested.
  <Exceptions>
     UnableToAcquireResourcesError
       If there are not enough resources in seattlegeni to fulfill the request.
  <Side Effects>
    None
  <Returns>
    A list of vessel lists. Each vessel list contains vessels on the same
    subnet. Each vessel list has a minimum of vesselcount availalable vessels
    on the user's port.
    
    The number of vessel lists (that is, the number of different subnets)
    returned may not include all possible subnets that seattlegeni knows about.
    This is for efficiency reasons. The maximum number of subnets returned
    can be adjusted through the GET_AVAILABLE_LAN_VESSELS_MAX_SUBNETS
    constant at the top of this module.
  """
  assert_geniuser(geniuser)
  assert_positive_int(vesselcount)
  
  subnetlist = _get_subnet_list()

  if len(subnetlist) == 0:
    raise UnableToAcquireResourcesError("No subnets exist with at least " + str(vesselcount) + " active nodes")
  
  subnets_vessels_list = []
  
  nonnatvesselsqueryset = _get_queryset_of_all_available_vessels_for_a_port_exclude_nat_nodes(geniuser.usable_vessel_port)
  
  for subnet in subnetlist:
    lanvesselsqueryset = nonnatvesselsqueryset.filter(node__last_known_ip__startswith=subnet + '.')
    
    if lanvesselsqueryset.count() >= vesselcount:
      # We don't worry about too many vessels being in this list, as it will be 255 at most.
      subnets_vessels_list.append(list(lanvesselsqueryset))

    if len(subnets_vessels_list) >= GET_AVAILABLE_LAN_VESSELS_MAX_SUBNETS:
      break

  if len(subnets_vessels_list) == 0:
    message = "No subnets exist with at least " + str(vesselcount)
    message += " active nodes that have a vessel available on port " + str(geniuser.usable_vessel_port)
    raise UnableToAcquireResourcesError(message)
  
  return subnets_vessels_list





@log_function_call
def get_user_free_vessel_credits(geniuser):
  """
  <Purpose>
    Determine number of free vessel credits the user gets (that is, vessel
    credits they get from registering an account without having donated any
    resources).
  <Arguments>
    geniuser
      The GeniUser object of the user whose freee vessel credit count is to be
      retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The user's number of free vessel credits.
  """
  assert_geniuser(geniuser)

  return geniuser.free_vessel_credits





@log_function_call
def get_user_vessel_credits_from_donations(geniuser):
  """
  <Purpose>
    Determine number of vessel credits the user has earned due to donations.
  <Arguments>
    geniuser
      The GeniUser object of the user whose vessel credits from donations are to
      be retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The user's number of vessel credits from donations.
  """
  assert_geniuser(geniuser)

  return len(get_donations_by_user(geniuser)) * VESSEL_CREDITS_FOR_DONATIONS_MULTIPLIER
  




@log_function_call
def get_user_total_vessel_credits(geniuser):
  """
  <Purpose>
    Determine the total number of vessel credits the user has, regardless of
    the number of vessels that already have acquired. This is the sum of the
    number of free vessel credits for the user and the number of vessel
    credits from donations by the user.
  <Arguments>
    geniuser
      The GeniUser object of the user whose total vessel credit count is to be
      retrieved.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    The user's total number of vessel credits.
  """
  return get_user_free_vessel_credits(geniuser) + get_user_vessel_credits_from_donations(geniuser) 
  




@log_function_call
def require_user_can_acquire_resources(geniuser, requested_vessel_count):
  """
  <Purpose>
    Ensure the user is allowed to acquire these resources. For now, only
    checks that a user has enough vessel credits for what they have requested.
    In the future, it could also check if the user was "banned".
    This isn't named assert_* because it doesn't raise an AssertionError
    when the user isn't allowed acquire resources.
  <Arguments>
    geniuser
    requested_vessel_count
  <Exceptions>
    InsufficientUserResourcesError
      If the user doesn't have enough vessel credits to satisfy the number
      of vessels the have requested.
  <Side Effects>
    None
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  assert_int(requested_vessel_count)
  
  # This isn't in the assertions module because it is all database-related
  # information. I wanted to avoid making the assertions module dependent
  # on maindb. If it's confusing, the name of this method can be changed.
  
  # This can be made faster. When necessary, add a get_acquired_vessels_count() function.
  acquired_vessel_count = len(get_acquired_vessels(geniuser))
  
  max_allowed_vessels = get_user_total_vessel_credits(geniuser)
  
  if requested_vessel_count + acquired_vessel_count > max_allowed_vessels:
    raise InsufficientUserResourcesError("Requested " + str(requested_vessel_count) + 
                                         " vessels, already acquired " + str(acquired_vessel_count) + 
                                         ", max allowed is " + str(max_allowed_vessels))





@log_function_call
def record_acquired_vessel(geniuser, vessel):
  """
  <Purpose>
    Performs all database operations necessary to record the fact that a vessel
    was acquired by a user.
  <Arguments>
    geniuser
      The GeniUser object of the user who is acquiring the vessel.
    vessel
      The Vessel object to be marked as acquired by the user.
  <Exceptions>
    None
  <Side Effects>
    The vessel is marked as acquired by geniuser. The user and vessel are
    also added to the database's VesselUserAccessMap table.
  <Returns>
    None
  """
  assert_geniuser(geniuser)
  assert_vessel(vessel)
  
  # We aren't caching any information with the user record about how many
  # resources have been acquired, so the only thing we need to do is make the
  # vessel as having been acquired by this user.
  vessel.acquired_by_user = geniuser
  vessel.date_acquired = datetime.now()
  vessel.date_expires = vessel.date_acquired + DEFAULT_VESSEL_EXPIRATION_TIMEDELTA
  vessel.save()
  
  # Update the database to reflect that this user has access to this vessel.
  add_vessel_access_user(vessel, geniuser)





@log_function_call
def record_released_vessel(vessel):
  """
  <Purpose>
    Performs all database operations necessary to record the fact that a vessel
    was released or expired.
  <Arguments>
    vessel
      The Vessel object to be marked as having been released.
  <Exceptions>
    None
  <Side Effects>
    The vessel is marked as not acquired by any user as well as marked as dirty.
    All records for this vessel in the database's VesselUserAccessMap have been
    removed.
  <Returns>
    None
  """
  assert_vessel(vessel)
  
  # We remove the VesselUserAccessMap records first just in case something
  # fails. That is, we don't want to leave the VesselUserAccessMap records
  # around with the vessel later getting cleaned up and given to another user.
  # Alternatively, we could manually commit a transaction for the
  # record_released_vessel() function that we're in to make sure all or none
  # of it gets done.
  _remove_all_user_access_to_vessel(vessel)
  
  # We aren't caching any information with the user record about how many
  # resources have been acquired, so the only thing we need to do is make the
  # vessel as having not having been acquired by any user.
  vessel.acquired_by_user = None
  vessel.is_dirty = True
  vessel.user_keys_in_sync = True
  vessel.date_acquired = None
  vessel.date_expires = None
  vessel.save()





def set_maximum_vessel_expiration(vessel):
  """
  <Purpose>
    Sets an acquired vessel's expiration date to the maximum allowed.
  <Arguments>
    vessel
      The Vessel object whose acquisition is to be extended.
  <Exceptions>
    None
  <Side Effects>
    The vessel's expiration date has been extended.
  <Returns>
    None
  """
  assert_vessel(vessel)
  
  vessel.date_acquired = datetime.now()
  vessel.date_expires = vessel.date_acquired + MAXIMUM_VESSEL_EXPIRATION_TIMEDELTA
  vessel.save()





# We don't log the function call here so that we don't fill up the backend
# daemon's logs.
def mark_expired_vessels_as_dirty():
  """
  <Purpose>
    Change all vessel records in the database whose acquisitions have expired
    to be marked as dirty in the database (that is, to indicate they need to
    be cleaned up by the backend).
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    All expired vessels (past expiration and acquired by users) in the database
    are marked as dirty as well as marked as not acquired by users. Additionally,
    all vessel user access map entries for each of these vessels have been
    removed.
  <Returns>
    The list of vessels that were marked as dirty.
  """
  # We want to mark as dirty all vessels past their expiration date that are
  # currently acquired by users.
  queryset = Vessel.objects.filter(date_expires__lte=datetime.now())
  queryset = queryset.exclude(acquired_by_user=None)
  
  vessel_list = list(queryset)
  
  if len(vessel_list) > 0:
    for vessel in vessel_list:
      record_released_vessel(vessel)

  # Return the number of vessels that just expired.
  return vessel_list





@log_function_call
def mark_vessel_as_clean(vessel):
  """
  <Purpose>
    Change the database to indicate that a vessel has been cleaned up by the
    backend.
  <Arguments>
    vessel
      The Vessel object of the vessel to be marked as clean.
  <Exceptions>
    None
  <Side Effects>
    Marks the vessel as clean in the database.
  <Returns>
    None
  """
  assert_vessel(vessel)
  
  vessel.is_dirty = False
  vessel.user_keys_in_sync = True
  vessel.save()





# We don't log the function call here so that we don't fill up the backend
# daemon's logs.
def get_vessels_needing_cleanup():
  """
  <Purpose>
    Determine which vessels need to be cleaned up by the backend.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects which are the vessels needing to be cleaned up.
  """
  queryset = Vessel.objects.filter(is_dirty=True)
  queryset = queryset.filter(node__is_active=True)
  queryset = queryset.filter(node__is_broken=False)
  # Be certain not to clean up vessels acquired by users. This is here mostly
  # in case an admin marked a vessel for cleanup that was acquired by a user.
  queryset = queryset.filter(acquired_by_user=None)
  return list(queryset)






@log_function_call
def does_vessel_need_cleanup(vessel):
  """
  <Purpose>
    Determine whether a given vessel needs to be cleaned up by the backend.
  <Arguments>
    vessel
      The Vessel object that we want to know if it needs to be cleaned up.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A tuple (needs_cleanup, reason) where needs_cleanup is a boolean indicating
    whether the vessel needs cleanup and reason is a string that indicates the
    reason cleanup is not needed if needs_cleanup is False.
  """
  assert_vessel(vessel)
  
  # Re-query the database in case this vessel has changed or been deleted.
  try:
    vessel = Vessel.objects.get(id=vessel.id)

  except django.core.exceptions.ObjectDoesNotExist:
    # The vessel was deleted.
    return (False, "The vessel no longer exists")
  
  if not vessel.node.is_active:
    return (False, "The node the vessel is on is not active")
  
  if vessel.node.is_broken:
    return (False, "The node the vessel is on is broken")
  
  if not vessel.is_dirty:
    return (False, "The vessel is not dirty")
  
  if vessel.acquired_by_user is not None:
    return (False, "The vessel is currently acquired")
  
  return (True, "")
  




def mark_vessel_as_needing_user_key_sync(vessel):
  """
  <Purpose>
    Set a vessel's database record to indicate that the vessel's user keys need
    to be sync'd.
  <Arguments>
    vessel
      The Vessel object of the vessel whose user keys are out of sync.
  <Exceptions>
    None
  <Side Effects>
    The database record the vessel is updated.
  <Returns>
    None.
  """
  assert_vessel(vessel)
  
  vessel.user_keys_in_sync = False
  vessel.save()





def mark_vessel_as_not_needing_user_key_sync(vessel):
  """
  <Purpose>
    Set a vessel's database record to indicate that the vessel's user keys do
    not need to be sync'd.
  <Arguments>
    vessel
      The Vessel object of the vessel whose user keys are in sync.
  <Exceptions>
    None
  <Side Effects>
    The database record the vessel is updated.
  <Returns>
    None.
  """
  assert_vessel(vessel)
  
  vessel.user_keys_in_sync = True
  vessel.save()





def get_vessels_needing_user_key_sync():
  """
  <Purpose>
    Determine which vessels need to have user keys sync'd by the backend.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects which are the vessels needing to have their
    user keys sync'd.
  """
  queryset = Vessel.objects.filter(user_keys_in_sync=False)
  queryset = queryset.filter(is_dirty=False)
  queryset = queryset.filter(node__is_active=True)
  queryset = queryset.filter(node__is_broken=False)
  
  return list(queryset)





def does_vessel_need_user_key_sync(vessel):
  """
  <Purpose>
    Determine whether a given vessel needs to have its user keys sync'd the
    backend.
  <Arguments>
    vessel
      The Vessel object that we want to know if it needs to have user keys
      sync'd.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A tuple (needs_sync, reason) where needs_sync is a boolean indicating
    whether the vessel needs user keys sync'd and reason is a string that
    indicates the reason key sync is not needed if needs_sync is False.
  """
  assert_vessel(vessel)
  
  # Re-query the database in case this vessel has changed or been deleted.
  try:
    vessel = Vessel.objects.get(id=vessel.id)

  except django.core.exceptions.ObjectDoesNotExist:
    # The vessel was deleted.
    return (False, "The vessel no longer exists")
  
  if not vessel.node.is_active:
    return (False, "The node the vessel is on is not active")
  
  if vessel.node.is_broken:
    return (False, "The node the vessel is on is broken")
  
  if vessel.is_dirty:
    return (False, "The vessel is dirty")
  
  return (True, "")





@log_function_call
def delete_all_vessels_of_node(node):
  """
  <Purpose>
    Delete from the database all vessel records of a node.
  <Arguments>
    node
      The Node object whose vessel records are to be deleted.
  <Exceptions>
    None
  <Side Effects>
    All vessel records for this node have been removed from the database.
  <Returns>
    None
  """
  assert_node(node)
  
  Vessel.objects.filter(node=node).delete()





def get_active_nodes():
  """
  <Purpose>
    Get a list of all active nodes that are not broken.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Node objects of active nodes that aren't broken.
  """
  return list(Node.objects.filter(is_active=True, is_broken=False))





def get_active_nodes_include_broken():
  """
  <Purpose>
    Get a list of all active nodes including those that are broken.
  <Arguments>
    None
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Node objects of active nodes.
  """
  return list(Node.objects.filter(is_active=True))





def get_vessels_on_node(node):
  """
  <Purpose>
    Get a list of all vessels on a nodes.
  <Arguments>
    node
      The Node object of the node we are interested in.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A list of Vessel objects of vessels on the node.
  """
  return list(node.vessel_set.all())




def create_action_log_event(function_name, user, second_arg, third_arg,
                            was_successful, message, date_started, vessel_list):
  
  delta = datetime.now() - date_started
  completion_time = ((delta.days * 3600 * 24) + 
                     delta.seconds + 
                     (delta.microseconds / 1000000.0))
  
  event = ActionLogEvent(function_name=function_name,
                         user=user,
                         second_arg=second_arg,
                         third_arg=third_arg,
                         was_successful=was_successful,
                         message=message,
                         vessel_count=len(vessel_list),
                         date_started=date_started,
                         completion_time=completion_time)
  
  event.save()
  
  for vessel in vessel_list:
    vesseldetails = ActionLogVesselDetails(event=event, node=vessel.node,
                                           node_address=vessel.node.last_known_ip,
                                           node_port=vessel.node.last_known_port,
                                           vessel_name=vessel.name)
    vesseldetails.save()
