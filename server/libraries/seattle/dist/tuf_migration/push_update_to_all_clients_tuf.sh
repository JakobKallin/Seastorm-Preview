#!/bin/bash

# Running this script will cause the updatesite directory checked by clients
# to be updated with the current files in the trunk directory. It will not
# automatically update trunk, so if you have a specfic revision checked out,
# that's what will be used. See constants below.
#
# You will need sudo privileges to use this. Don't run this as sudo, it will
# invoke sudo when it needs it.
#
# Usage: ./push_update_to_all_clients.sh

TRUNK_DIR=/path/to/trunk
PUBLIC_KEY_FILE=/path/to/softwareupdater/pub/key
PRIVATE_KEY_FILE=/path/to/softwareupdater/priv/key
KEYSTORE_DIR=/path/to/keystore.txt

UPDATE_URL=url://of_softwareupdate_site

UPDATESITE_DIR=/sofwareupdater/server/dir
DEBUG_UPDATESITE_DIR=$UPDATESITE_DIR-test


# Make sure the updateurl is correct.
UPDATE_URL_FOUND=$(grep -F "seattle_url = \"$UPDATE_URL\"" $TRUNK_DIR/softwareupdater/softwareupdater.py)

if [ "$UPDATE_URL_FOUND" == "" ]; then
  echo "Did not find the correct update url in $TRUNK_DIR/softwareupdater/softwareupdater.py"
  exit 1
fi

if [ "$1" != "" ]; then
  # Note that the -d option in update_software.py isn't a really convincing idea if you can
  # just pass a different directory.
  UPDATESITE_DIR=$DEBUG_UPDATESITE_DIR
  echo "An argument was provided. Using debug mode (so, putting files in $UPDATESITE_DIR)."
fi

# The update_software.py script does weird things if the directory doesn't already exist,
# such as creating a file with the name of the directory.
if [ ! -d "$UPDATESITE_DIR" ]; then
  sudo mkdir $UPDATESITE_DIR
  if [ "$?" != "0" ]; then
    echo "Failed to create missing directory $UPDATESITE_DIR."
    exit 1
  fi
fi

UPDATESITE_BACKUP_DIR=$UPDATESITE_DIR.backups

# Make sure there's a directory to backup the update directory to.
if [ ! -d "$UPDATESITE_BACKUP_DIR" ]; then
  sudo mkdir $UPDATESITE_BACKUP_DIR
fi

# Backup the current updatesite.
DATE=`date +%s`
echo "Backing up $UPDATESITE_DIR to $UPDATESITE_BACKUP_DIR/$DATE"
sudo cp -a $UPDATESITE_DIR $UPDATESITE_BACKUP_DIR/$DATE

sudo python $TRUNK_DIR/dist/update_seattle_tuf.py $TRUNK_DIR $PUBLIC_KEY_FILE $PRIVATE_KEY_FILE $KEYSTORE_DIR $UPDATESITE_DIR

echo "Done."

