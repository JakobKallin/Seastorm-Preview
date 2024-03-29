""" 
Author: Justin Cappos

Module: Optimized routines that use python's crypto to
        interact with a node manager to perform actions on
        nodes.   A simple front end can be added to make this a functional
        experiment manager.

Start date: September 7th 2008

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

"""

# JAC: This is the only change to the file over the nmclient.repy version...
# for signing the data we send to the node manager
import fastsigneddata

from repyportability import *
add_dy_support(locals())


# session wrapper (breaks the stream into messages)
# an abstracted "itemized data communication" in a separate API
dy_import_module_symbols("session.repy")


# makes connections time out
dy_import_module_symbols("sockettimeout.repy")

# For rsa key conversion.
dy_import_module_symbols("rsa.repy")

dy_import_module_symbols("time.repy")
# The idea is that this module returns "node manager handles".   A handle
# may be used to communicate with a node manager and issue commands.   If the
# caller wants to have a set of node managers with the same state, this can
# be done by something like:
#
#
# myid =    # some unique, non-repeating value
# nmhandles = []
# for nm in nodemanagers:
#   nmhandles.append(nmclient_createhandle(nm, sequenceid = myid))
#
# 
# def do_action(action):
#   for nmhandle in nmhandles:
#     nmclient_doaction(nmhandle, ... )
#
#
# The above code snippet will ensure that none of the nmhandles perform the
# actions called in do_action() out of order.   A node that "misses" an action
# (perhaps due to a network or node failure) will not perform later actions 
# unless the sequenceid is reset.
#
# Note that the above calls to nmclient_createhandle and nmclient_doaction 
# should really be wrapped in try except blocks for NMClientExceptions



# Thrown when a failure occurs when trying to communicate with a node
class NMClientException(Exception):
  pass

# This holds all of the client handles.   A client handle is merely a 
# string that is the key to this dict.   All of the information is stored in
# the dictionary value (a dict with keys for IP, port, sessionID, timestamp,
# identity, expirationtime, public key, private key, and vesselID).   
nmclient_handledict = {}

# BUG: How do I do this and have it be portable across repy <-> python?
# needed when assigning new handles to prevent race conditions...
nmclient_handledictlock = createlock()



# Note: I open a new connection for every request.   Is this really what I want
# to do?   It seemed easiest but likely has performance implications

# Sends data to a node (opens the connection, writes the 
# communication header, sends all the data, receives the result, and returns
# the result)...
def nmclient_rawcommunicate(nmhandle, *args):

  # the node is behind a nat and using nat layer
  if 'natlayermac' in nmclient_handledict[nmhandle]:
    try:
      # add 5 to timeout for nat delay
      thisconnobject = nat_openconn(nmclient_handledict[nmhandle]['natlayermac'],nmclient_handledict[nmhandle]['port'],timeout=nmclient_handledict[nmhandle]['timeout']+5,usetimeoutsock=True) 
    except Exception, e:
      raise NMClientException, str(e)
  
  # not a NATLayer connection
  else:
    # do the normal openconn
    try:
      thisconnobject = timeout_openconnection(nmclient_handledict[nmhandle]['IP'], nmclient_handledict[nmhandle]['port'],timeout=nmclient_handledict[nmhandle]['timeout']) 
    except Exception, e:
      raise NMClientException, str(e)

  
  # always close the connobject
  try:

    # send the args separated by '|' chars (as is expected by the node manager)
    session_sendmessage(thisconnobject, '|'.join(args))
    return session_recvmessage(thisconnobject)
  except Exception, e:
    raise NMClientException, str(e)
  finally:
    thisconnobject.close()




# Sends data to a node (opens the connection, writes the 
# communication header, sends all the data, receives the result, and returns
# the result)...
def nmclient_signedcommunicate(nmhandle, *args):
  
  # need to check lots of the nmhandle settings...

  if nmclient_handledict[nmhandle]['timestamp'] == True:
    # set the time based upon the current time...
    timestamp = time_gettime()
  elif not nmclient_handledict[nmhandle]['timestamp']:
    # we're false, so set to None
    timestamp = None
  else:
    # For some reason, the caller wanted a specific time...
    timestamp = nmclient_handledict[nmhandle]['timestamp']

  if nmclient_handledict[nmhandle]['publickey']:
    publickey = nmclient_handledict[nmhandle]['publickey']
  else:
    raise NMClientException, "Must have public key for signed communication"

  if nmclient_handledict[nmhandle]['privatekey']:
    privatekey = nmclient_handledict[nmhandle]['privatekey']
  else:
    raise NMClientException, "Must have private key for signed communication"

  # use this blindly (None or a value are both okay)
  sequenceid = nmclient_handledict[nmhandle]['sequenceid']

  if nmclient_handledict[nmhandle]['expiration']:
    if timestamp == None:
      # highly dubious.   However, it's technically valid, so let's allow it.
      expirationtime = nmclient_handledict[nmhandle]['expiration']
    else:
      expirationtime = timestamp + nmclient_handledict[nmhandle]['expiration']

  else:
    # they don't want this to expire
    expirationtime = nmclient_handledict[nmhandle]['expiration']


  # use this blindly (None or a value are both okay)
  identity = nmclient_handledict[nmhandle]['identity']


  # build the data to send.   Ideally we'd do: datatosend = '|'.join(args)
  # we can't do this because some args may be non-strings...
  datatosend = args[0]
  for arg in args[1:]:
    datatosend = datatosend + '|' + str(arg)
  

  # Sign first before opening the connection to prevent connections from idling
  try:
    signeddata = fastsigneddata.signeddata_signdata(datatosend, privatekey, publickey, timestamp, expirationtime, sequenceid, identity)
  except ValueError, e:
    raise NMClientException, str(e)


  # the node is behind a nat
  if 'natlayermac' in nmclient_handledict[nmhandle]:
    try:
      # add 5 to timeout for nat delay
      thisconnobject = nat_openconn(nmclient_handledict[nmhandle]['natlayermac'], nmclient_handledict[nmhandle]['port'],timeout=nmclient_handledict[nmhandle]['timeout']+5,usetimeoutsock=True) 
    except Exception, e:
      raise NMClientException, str(e)
  
  # not a natlayer conn
  else:  

    try:
      thisconnobject = timeout_openconnection(nmclient_handledict[nmhandle]['IP'], nmclient_handledict[nmhandle]['port'], timeout=nmclient_handledict[nmhandle]['timeout'])
    except Exception, e:
      raise NMClientException, str(e)

  
  # always close the connobject afterwards...
  try:
    try:
      session_sendmessage(thisconnobject, signeddata)
    except Exception, e:
      # label the exception and change the type...
      raise NMClientException, "signedcommunicate failed on session_sendmessage with error '"+str(e)+"'"

    try:
      message = session_recvmessage(thisconnobject)
    except Exception, e:
      # label the exception and change the type...
      raise NMClientException, "signedcommunicate failed on session_recvmessage with error '"+str(e)+"'"

    return message
  finally:
    thisconnobject.close()



def nmclient_safelygethandle():
  # I lock to prevent a race when adding handles to the dictionary.   I don't
  # need a lock when removing because a race is benign (it prevents reuse)
  nmclient_handledictlock.acquire(True)
  try:
    potentialhandle = randomfloat()
    while potentialhandle in nmclient_handledict:
      potentialhandle = randomfloat()

    # Added to fix #885.   This ensures that the handle won't be reused
    nmclient_handledict[potentialhandle] = {}

    return potentialhandle
  finally:
    nmclient_handledictlock.release()





# Create a new handle, the IP, port must be provided but others are optional.
# The default is to have no sequenceID, timestamps on, expiration time of 1 
# hour, and the program should set and use the identity of the node.   The 
# public key, private key, and vesselids are left uninitialized unless 
# specified elsewhere.   Regardless, the keys and vesselid are not used to 
# create the handle and so are merely transfered to the created handle.
# Per #537, the default timeout (15) should be greater than the wait period 
# for starting a vessel.
def nmclient_createhandle(nmIP, nmport, sequenceid = None, timestamp=True, identity = True, expirationtime = 60*60, publickey = None, privatekey = None, vesselid = None, timeout=15):

  thisentry = {}

  # is this using the nat layer  NAT$MAC
  if 'NAT' in nmIP:
    (_,mac) = nmIP.split('$')
    thisentry['natlayermac'] = mac 


  thisentry['IP'] = nmIP
  thisentry['port'] = nmport
  thisentry['sequenceid'] = sequenceid
  thisentry['timestamp'] = timestamp
  thisentry['expiration'] = expirationtime
  thisentry['publickey'] = publickey
  thisentry['privatekey'] = privatekey
  thisentry['vesselid'] = vesselid
  thisentry['timeout'] = timeout

    
  newhandle = nmclient_safelygethandle()

  nmclient_handledict[newhandle] = thisentry

  # Use GetVessels as a "hello" test (and for identity reasons as shown below)
  try:
    response = nmclient_rawsay(newhandle, 'GetVessels')

  except (ValueError, NMClientException, KeyError), e:
    del nmclient_handledict[newhandle]
    raise NMClientException, e


  # set up the identity
  if identity == True:
    for line in response.split('\n'):
      if line.startswith('Nodekey: '):
        # get everything after the Nodekey as the identity
        nmclient_handledict[newhandle]['identity'] = line[len('Nodekey: '):]
        break
        
    else:
      del nmclient_handledict[newhandle]
      raise NMClientException, "Do not understand node manager identity in identification"

  else:
    nmclient_handledict[newhandle]['identity'] = identity

  # it worked!
  return newhandle



def nmclient_duplicatehandle(nmhandle):
  newhandle = nmclient_safelygethandle()
  nmclient_handledict[newhandle] = nmclient_handledict[nmhandle].copy()
  return newhandle

# public.   Use this to clean up a handle
def nmclient_destroyhandle(nmhandle):
  try:
    del nmclient_handledict[nmhandle]
  except KeyError:
    return False
  return True
  

# public.   Use these to get / set attributes about the handles...
def nmclient_get_handle_info(nmhandle):
  if nmhandle not in nmclient_handledict:
    raise NMClientException, "Unknown nmhandle: '"+str(nmhandle)+"'"
  return nmclient_handledict[nmhandle].copy()


def nmclient_set_handle_info(nmhandle, dict):
  if nmhandle not in nmclient_handledict:
    raise NMClientException, "Unknown nmhandle: '"+str(nmhandle)+"'"
  nmclient_handledict[nmhandle] = dict


  

# Public:  Use this for non-signed operations...
def nmclient_rawsay(nmhandle, *args):
  fullresponse = nmclient_rawcommunicate(nmhandle, *args)

  try:
    (response, status) = fullresponse.rsplit('\n',1)
  except KeyError:
    raise NMClientException, "Communication error '"+fullresponse+"'"

  if status == 'Success':
    return response
  elif status == 'Error':
    raise NMClientException, "Node Manager error '"+response+"'"
  elif status == 'Warning':
    raise NMClientException, "Node Manager warning '"+response+"'"
  else:
    raise NMClientException, "Unknown status '"+fullresponse+"'"
  



# Public:  Use this for signed operations...
def nmclient_signedsay(nmhandle, *args):

  fullresponse = nmclient_signedcommunicate(nmhandle, *args)

  try:
    (response, status) = fullresponse.rsplit('\n',1)
  except KeyError:
    raise NMClientException, "Communication error '"+fullresponse+"'"

  if status == 'Success':
    return response
  elif status == 'Error':
    raise NMClientException, "Node Manager error '"+response+"'"
  elif status == 'Warning':
    raise NMClientException, "Node Manager warning '"+response+"'"
  else:
    raise NMClientException, "Unknown status '"+fullresponse+"'"
  


# public, use this to do raw communication with a vessel
def nmclient_rawsaytovessel(nmhandle, call, *args):
  vesselid = nmclient_handledict[nmhandle]['vesselid']
  if not vesselid:
    raise NMClientException, "Must set vesselid to communicate with a vessel"

  return nmclient_rawsay(nmhandle,call, vesselid,*args)
  


# public, use this to do a signed communication with a vessel
def nmclient_signedsaytovessel(nmhandle, call, *args):
  vesselid = nmclient_handledict[nmhandle]['vesselid']
  if not vesselid:
    raise NMClientException, "Must set vesselid to communicate with a vessel"

  return nmclient_signedsay(nmhandle,call, vesselid,*args)


# public, lists the vessels that the provided key owns or can use
def nmclient_listaccessiblevessels(nmhandle, publickey):

  vesselinfo = nmclient_getvesseldict(nmhandle)

  # these will be filled with relevant vessel names...
  ownervessels = []
  uservessels = []

  for vesselname in vesselinfo['vessels']:
    if publickey == vesselinfo['vessels'][vesselname]['ownerkey']:
      ownervessels.append(vesselname)

    if 'userkeys' in vesselinfo['vessels'][vesselname] and publickey in vesselinfo['vessels'][vesselname]['userkeys']:
      uservessels.append(vesselname)


  return (ownervessels, uservessels)



#public, parse a node manager's vessel information and return it to the user...
def nmclient_getvesseldict(nmhandle):

  response = nmclient_rawsay(nmhandle, 'GetVessels')

  retdict = {}
  retdict['vessels'] = {}

  # here we loop through the response and set the dicts as appropriate
  lastvesselname = None
  for line in response.split('\n'):
    if not line:
      # empty line.   Let's allow it...
      pass
    elif line.startswith('Version: '):
      retdict['version'] = line[len('Version: '):]
    elif line.startswith('Nodename: '):
      retdict['nodename'] = line[len('Nodename: '):]
    elif line.startswith('Nodekey: '):
      retdict['nodekey'] = rsa_string_to_publickey(line[len('Nodekey: '):])
 
    # start of a vessel
    elif line.startswith('Name: '):
      # if there is a previous vessel write it to the dict...
      if lastvesselname:
        retdict['vessels'][lastvesselname] = thisvessel

      thisvessel = {}
      # NOTE:I'm changing this so that userkeys will always exist even if there
      # are no user keys (in this case it has an empty list).   I think this is
      # the right functionality.
      thisvessel['userkeys'] = []
      lastvesselname = line[len('Name: '):]

    elif line.startswith('OwnerKey: '):
      thiskeystring = line[len('OwnerKey: '):]
      thiskey = rsa_string_to_publickey(thiskeystring)
      thisvessel['ownerkey'] = thiskey

    elif line.startswith('OwnerInfo: '):
      thisownerstring = line[len('OwnerInfo: '):]
      thisvessel['ownerinfo'] = thisownerstring

    elif line.startswith('Status: '):
      thisstatus = line[len('Status: '):]
      thisvessel['status'] = thisstatus

    elif line.startswith('Advertise: '):
      thisadvertise = line[len('Advertise: '):]
      if thisadvertise == 'True':
        thisvessel['advertise'] = True
      elif thisadvertise == 'False':
        thisvessel['advertise'] = False
      else:
        raise NMClientException, "Unknown advertise type '"+thisadvertise+"'"

    elif line.startswith('UserKey: '):
      thiskeystring = line[len('UserKey: '):]
      thiskey = rsa_string_to_publickey(thiskeystring)

      thisvessel['userkeys'].append(thiskey)

    else:
      raise NMClientException, "Unknown line in GetVessels response '"+line+"'"


  if lastvesselname:
    retdict['vessels'][lastvesselname] = thisvessel
  return retdict
