#!/usr/bin/env python
"""
<Purpose>
  This script is used to immediately stop everything running on behalf of a given
  seattle user, remove the resources allocated to them, and restrict them from
  acquiring more resources.

  Usage:
    ./ban_user_and_stop_vessels.py <geni_username>

  You will be given status information as the process is completed, including
  any nodes that can't be communicated with (meaning that the user's vessels
  on that node haven't been taken away from them).
"""

import sys
import time

from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb
from seattlegeni.common.util import log
from seattlegeni.website.control import vessels

from seattlegeni.common.exceptions import *


# Set the log level high enough so that we don't produce a bunch of logging
# output due to the logging decorators.
initial_log_level = log.loglevel
log.set_log_level(log.LOG_LEVEL_INFO)



def ban_user_and_remove_vessels(username):

  try:
    geniuser = maindb.get_user(username, allow_inactive=True)
  except DoesNotExistError:
    print "No such user: %s." % username
    sys.exit(1)

  # Lock the user.
  lockserver_handle = lockserver.create_lockserver_handle()
  lockserver.lock_user(lockserver_handle, geniuser.username)

  try:
    if geniuser.is_active:
      geniuser.is_active = False
      geniuser.save()
      print "This account has been set to inactive (banned)."
    else:
      print "This account is already inactive (banned)."

    acquired_vessels = maindb.get_acquired_vessels(geniuser)
    if not acquired_vessels:
      print "No acquired vessels to stop/remove access to."
    else:
      print "Vessels acquired by this user: %s" % acquired_vessels
      print "Indicating to the backend to release %s vessels." % len(acquired_vessels)
      vessels.release_vessels(lockserver_handle, geniuser, acquired_vessels)
      print "Release indicated. Monitoring db to see if the backend cleaned them up."
      while True:
        for vessel in acquired_vessels[:]:
          updated_vessel = maindb.get_vessel(vessel.node.node_identifier, vessel.name)
          if vessel.node.is_broken or not vessel.node.is_active:
            print "Node %s is broken or inactive, so backend won't contact it." % vessel.node
            acquired_vessels.remove(vessel)
            continue

          if updated_vessel.is_dirty:
            print "Vessel %s has not been cleaned up yet." % updated_vessel
          else:
            print "Vessel %s has been cleaned up." % updated_vessel
            acquired_vessels.remove(vessel)

        if not acquired_vessels:
          print "All vessels have been cleaned up."
          break
        else:
          print "%s vessels remain to be cleaned up." % len(acquired_vessels)

        print "Sleeping 10 seconds."
        time.sleep(10)

  finally:
    # Unlock the user.
    lockserver.unlock_user(lockserver_handle, geniuser.username)
    lockserver.destroy_lockserver_handle(lockserver_handle)


if __name__ == "__main__":
  if len(sys.argv) != 2:
    print "Usage: ./ban_user_and_stop_vessels.py <geni_username>"
    sys.exit(1)
  ban_user_and_remove_vessels(sys.argv[1])
