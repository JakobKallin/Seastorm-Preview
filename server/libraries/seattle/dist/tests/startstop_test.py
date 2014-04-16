"""
<Program Name>
  startstop_test.py

<Started>
  June 4, 2009

<Author>
  Zachary Boka

<Purpose>
  Prints out the processes holding the keys: "seattlenodemanager",
  "softwareupdater.old", "softwareupdater.new".

  Designed to be run before and after the start_seattle and stop_seattle scripts
  in order to confirm that the node manager and software updater were indeed
  started or stopped by the corresponding start_seattle and stop_seattle script.
 """

import runonce
import os
import time


locklist = ["seattlenodemanager", "softwareupdater.old", "softwareupdater.new"]


def main():
  # Give time for any changes in acquiring/relinquishing keys to take effect
  time.sleep(2)
  for lockname in locklist:
    status = runonce.getprocesslock(lockname)
    if status == True:
      print "The lock '" + lockname + "' was not being held."
      runonce.releaseprocesslock(lockname)
    elif status == False:
      print "There was an error getting the lock '" + lockname + "'."
    else:
      print "The lock '" + lockname + "' is currently being used by process pid: " + str(status)



if __name__ == '__main__':
  main()
