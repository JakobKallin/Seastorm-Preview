#!/bin/bash

# This script will migrate the current software updater to the 
# TUF software updater.

# Set the various variables that are needed.
trunk_dir=/home/testgeni/trunk

tuf_server_dir=/var/www/tuf_updatesite
tuf_server_url="http://blackbox.cs.washington.edu/tuf_updatesite/"

temp_server_dir=/var/www/migrate_updatesite
temp_server_url="http://blackbox.cs.washington.edu/migrate_updatesite/"

current_server_dir=/var/www/updatesite
current_server_url="http://blackbox.cs.washington.edu/updatesite/"

public_key_file=/path/to/pubkey
private_key_file=/path/to/privkey
keystore_dir=/path/to/keystore

# Some convenient paths that are used multiple times.
cur_softwareupdater_path=$trunk_dir/softwareupdater/softwareupdater.py
temp_softwareupdater_path=$trunk_dir/dist/tuf_migration/migrating_softwareupdater.py
migration_dir=$trunk/dist/tuf_migration


# We are going to attempt to migrate from the old software updater
# to the new and more secure TUF based sofwtware updater. This
# requires 3 different steps. The current software updater is unable
# to download directories as part of its update. To get around this,
# we have a modified software updater that can download a tar file
# and untar the contents of the file in its directory. So the first
# step in this migrations is that we will push a new software 
# updater that will be able to download tar files and untar its 
# contents. In the second step, we are going to push some  tar
# files that have all the contents that are required by the new TUF
# software updater. We are also going to push the TUF software 
# updater through the old software updater. At this point the client
# should have the new TUF software updater, and all the files that is
# required to run the new TUF software updater. In step three we are
# going to create a server for the TUF software updater to contact to.
# This script is going to create two new servers, and push an update
# through the current server. We are going to do all the steps 
# backward so the client does not break at any time.


#######################################
# Step 1: Create the TUF server.
#######################################

if [ ! -d "$tuf_server_dir" ]; then
  sudo mkdir $tuf_server_dir
  if [ "$?" != "0" ]; then
    echo "Failed to create missing directory $tuf_server_dir"
    exit 1
  fi
fi

backup_server_dir=$tuf_server_dir.backups

# Make sure there's a directory to backup the update directory to.
if [ ! -d "$backup_server_dir" ]; then
  sudo mkdir $backup_server_dir
fi

# Backup the current updatesite.
cur_date=`date +%s`
echo "Backing up $tuf_server_dir to $backup_server_dir/$cur_date"
sudo cp -a $tuf_server_dir $backup_server_dir/$cur_date

# Create a new Tuf Server.
echo "Creating a new tuf server at: $tuf_server_dir"
python $trunk_dir/dist/create_softwareupdater_server.py $trunk_dir $public_key_file $private_key_file $keystore_dir $tuf_server_dir
echo "Finished creating new TUF server"





###################################################################
# Step 2: Create a migrating server that distributes tuf files.
###################################################################

# Ensure that the migrating server directory exists.
if [ ! -d "$temp_server_dir" ]; then
  sudo mkdir $temp_server_dir
  if [ "$?" != "0" ]; then
    echo "Failed to create missing directory $tuf_server_dir"
    exit 1
  fi
fi

# Copy over the repo files.
echo "Copying all the tuf related files..."
python cp_repo_files.py $trunk_dir/dist/tuf_migration $tuf_server_dir

# Create the tarred files of the tuf files that are needed for TUF
# software updater.
tar -cvvf $migration_dir/tuf.tar $trunk_dir/tuf/ --exclude="*.svn*"
tar -cvvf $migration_dir/simplejson.tar $trunk_dir/tuf/simplejson --exclude="*.svn*"
tar -cvvf $migration_dir/repo.tar $trunk_dir/dist/tuf_migration/repo/ --exclude="*.svn*"

cp $migration_dir/*.tar $trunk_dir/softwareupdater/

# We no longer need the repo directory, once its tarred.
rm -rf $migration_dir/repo/
echo "Finished copying tuf related files."


# Before we push everything to the server, we want to ensure that the
# softwareupdater url embedded into the softwareupdater.py is correct.
updater_url_found=$(grep -F "seattle_url = \"$tuf_server_url\"" $trunk_dir/softwareupdater/softwareupdater.py)

if [ "$update_url_found" == "" ]; then
  echo "Did not find the correct update url in $trunk_dir/softwareupdater/softwareupdater.py"
  rm $migration_dir/*.tar
  exit 1
fi


# Create the temporary migrating directory.
echo "Creating temporary migrating updater server..."
/bin/bash $migration_dir/push_update_to_all_clients.sh $trunk_dir $public_key_file $private_key_file $temp_server_url $temp_server_dir
rm $migration_dir/*.tar
echo "Finished creating the temporary migrating updater server."





###################################################################
# Step 3: Pushing the modified software updater.
###################################################################

# Copy over the temporary software updater.
echo "Copying the modified software updater"
cp $cur_softwareupdater_path $migration_dir/softwareupdater.py.bak
cp $temp_softwareupdater_path $cur_softwareupdater_path


# Before we push everything to the server, we want to ensure that the
# softwareupdater url embedded into the softwareupdater.py is correct.
temp_updater_url_found=$(grep -F "softwareurl = \"$temp_server_url\"" $trunk_dir/softwareupdater/softwareupdater.py)

if [ "$temp_updater_url_found" == "" ]; then
  echo "Did not find the correct update url in $temp_softwareupdater_path"
  mv $migration_dir/softwareupdater.py.bak $cur_softwareupdater_path
  rm $migration_dir/softwareupdater.py.bak
  exit 1
fi


echo "Starting to push the modified softwareupdater..."
/bin/bash $migration_dir/push_update_to_all_clients.sh $trunk_dir $public_key_file $private_key_file $current_server_url $current_server_dir

# Restore the non-modified software updater
mv $migration_dir/softwareupdater.py.bak $cur_softwareupdater_path 

echo "Finished pushing the modified softwareupdater."
echo "The clients should now start to migrate from the old software updater to the TUF software updater.