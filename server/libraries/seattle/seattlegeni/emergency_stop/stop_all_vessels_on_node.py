#!/usr/bin/env python
"""
<Purpose>
  This script is used to immediately stop everything running on a node.

  Usage:
    ./stop_all_vessels_on_node.py "<node_id>"

  Note that the node_id contains a space, so you need to put it in quotes.

  You will be given status information as the process is completed.
"""

import sys
import time

from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb
from seattlegeni.common.util import log

from seattlegeni.common.exceptions import *


# Set the log level high enough so that we don't produce a bunch of logging
# output due to the logging decorators.
initial_log_level = log.loglevel
log.set_log_level(log.LOG_LEVEL_INFO)



def stop_all_vessels_on_node(node_id):

  try:
    node = maindb.get_node(node_id)
  except DoesNotExistError:
    print "No such node"
    sys.exit(1)

  if not node.is_active:
    print "This node is marked as inactive, thus the backend will not try to clean up vessels."
    sys.exit(0)

  if node.is_broken:
    print "This node is marked as broken, thus the backend will not try to clean up vessels."
    sys.exit(0)

  vessels_on_node = maindb.get_vessels_on_node(node)
  if not vessels_on_node:
    print "No vessels on node."
    sys.exit(0)

  lockserver_handle = lockserver.create_lockserver_handle()
  try:
    print "Indicating to the backend to release/reset all %s vessels." % len(vessels_on_node)
    lockserver.lock_node(lockserver_handle, node_id)
    try:
      for vessel in vessels_on_node:
        maindb.record_released_vessel(vessel)
    finally:
      lockserver.unlock_node(lockserver_handle, node_id)

    print "Releases indicated. Monitoring db to see if the backend cleaned them up."
    while True:
      for vessel in vessels_on_node[:]:
        updated_vessel = maindb.get_vessel(node_id, vessel.name)
        if updated_vessel.is_dirty:
          print "Vessel %s has not been cleaned up yet." % updated_vessel
        else:
          print "Vessel %s has been cleaned up." % updated_vessel
          vessels_on_node.remove(vessel)
      if not vessels_on_node:
        print "All vessels have been cleaned up."
        break
      else:
        print "%s vessels remain to be cleaned up." % len(vessels_on_node)
      print "Sleeping 10 seconds."
      time.sleep(10)

  finally:
    lockserver.destroy_lockserver_handle(lockserver_handle)


if __name__ == "__main__":
  if len(sys.argv) != 2:
    print 'Usage: ./stop_all_vessels_on_node.py "<node_id>"'
    sys.exit(1)
  maindb.init_maindb()
  stop_all_vessels_on_node(sys.argv[1])
