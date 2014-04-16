#!/bin/bash

# <Author>
#   Justin Samuel
# <Date Started>
#   August 13, 2009
# <Purpose>
#   This script updates the /home/geni/trunk from svn trunk and then redeploys
#   the seattlegeni files to /home/geni/live. This script is the intended way
#   to update seattlegeni from trunk on the production server. The
#   configuration files will be maintained.
#
#   A backup of the replaced version of seattlegeni will be left in the
#   /home/geni/bak directory.
# 
#   After running this script, you probably want to kill the existing running
#   copy of start_seattlegeni_components.sh and start that script again. This
#   will result in all seattlegeni components running off of the newly deployed
#   version.
# <Usage>
#    As root:
#    update_seattlegeni_from_trunk.sh

if [ "$USER" != "root" ]; then
  echo "You must run this script as root. Exiting."
  exit 1
fi

SUDO_CMD="sudo -u geni"

cd /home/geni

$SUDO_CMD svn up trunk/

$SUDO_CMD python trunk/seattlegeni/deploymentscripts/deploy_seattlegeni.py trunk/ live/

$SUDO_CMD mv live.bak.* bak/

# Ensure that sensitive files are only readable by the geni user:
chown geni live/seattlegeni/keydb/config.py
chown geni live/seattlegeni/backend/config.py
chmod 600 live/seattlegeni/keydb/config.py
chmod 600 live/seattlegeni/backend/config.py

