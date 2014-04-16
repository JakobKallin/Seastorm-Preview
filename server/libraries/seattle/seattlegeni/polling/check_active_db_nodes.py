"""
<Program>
  check_active_db_nodes.py

<Started>
  16 August 2009

<Author>
  Justin Samuel

<Purpose>
  This script runs an infinite loop of checks over all of the active nodes in
  the database. It will result in inactive and broken nodes or vessels needing
  release/cleanup being marked as such in the database.
  
  This is the only place in seattlegeni where we ensure that nodes that have
  gone offline and no longer advertise get marked as inactive in the database.
  
  This script will not directly result in any state-changing nodemanager
  communication (only node information querying). It uses the check_node()
  function in the seattlegeni.common.util.nodestatus module, which means
  that only the database will be directly modified.
"""

import django.core.mail
import django.db

import sys
import time
import traceback

from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb

from seattlegeni.common.util import log

from seattlegeni.common.exceptions import *

from seattlegeni.common.util import nodestatus

from seattlegeni.website import settings



# The number of seconds to sleep at the end of each iteration through all
# active nodes in the database. This only applies when running this as a
# script.
SLEEP_SECONDS_BETWEEN_RUNS = 60

# If True, no database changes will be made marking nodes as inactive or broken
# when this is run as a script. This is independent of the readonly argument
# that can be passed to check_node() if check_node() is called directly from
# another module.
READONLY = False





def main():
  """
  This will run an infinite loop of checks over all of the active nodes in the
  database.
  """
  
  lockserver_handle = lockserver.create_lockserver_handle()

  # Always try to release the lockserver handle, though it's probably not
  # very useful in this case.
  try:
    
    while True:
      
      # Catch unexpected exceptions to log/send mail.
      try:
      
        # We shouldn't be running in production with settings.DEBUG = True. 
        # Just in case, though, tell django to reset its list of saved queries
        # each time through the loop.
        if settings.DEBUG:
          django.db.reset_queries()
        
        # Note: although we include broken but active nodes, we don't change
        # the status of broken nodes to be not broken yet if we don't detect
        # any problems. For now, most of the reason we include broken nodes
        # is so that we can tell which broken nodes are still online. This is
        # because it's not as big of a concern to have a broken node that is
        # quickly offline (e.g. broken nodes in development), but having one be
        # online for an extended period of time is a stronger signal of
        # potentially unknown bugs in the seattlegeni or seattle code.
        active_nodes = maindb.get_active_nodes_include_broken()
        log.info("Starting check of " + str(len(active_nodes)) + " active nodes.")
      
        checked_node_count = 0
        
        for node in active_nodes:
          
          checked_node_count += 1
          log.info("Checking node " + str(checked_node_count) + ": " + str(node))
          
          nodestatus.check_node(node, readonly=READONLY, lockserver_handle=lockserver_handle)
          
        # Print summary info.
        log.info("Nodes checked: " + str(checked_node_count))
        nodes_with_problems = nodestatus.get_node_problem_info()
        nodes_with_problems_count = len(nodes_with_problems.keys())
        log.info("Nodes without problems: " + str(checked_node_count - nodes_with_problems_count))
        log.info("Nodes with problems: " + str(nodes_with_problems_count))
        
        # Print information about the database changes made.
        log.info("Number of database actions taken:")
        actionstaken = nodestatus.get_actions_taken()
        for actionname in actionstaken:
          log.info("\t" + actionname + ": " + str(len(actionstaken[actionname])) + 
                   " " + str(actionstaken[actionname]))
    
        nodestatus.reset_collected_data()
        
        log.info("Sleeping for " + str(SLEEP_SECONDS_BETWEEN_RUNS) + " seconds.")
        time.sleep(SLEEP_SECONDS_BETWEEN_RUNS)
  
      except KeyboardInterrupt:
        raise
  
      except:
        message = "Unexpected exception in check_active_db_nodes.py: " + traceback.format_exc()
        log.critical(message)
    
        # Send an email to the addresses listed in settings.ADMINS
        if not settings.DEBUG:
          subject = "Critical SeattleGeni check_active_db_nodes.py error"
          django.core.mail.mail_admins(subject, message)
          
          # Sleep for ten minutes to make sure we don't flood the admins with error
          # report emails.
          time.sleep(600)

  finally:
    lockserver.destroy_lockserver_handle(lockserver_handle)
  
  



if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    log.info("Exiting on KeyboardInterrupt.")
    sys.exit(0)
