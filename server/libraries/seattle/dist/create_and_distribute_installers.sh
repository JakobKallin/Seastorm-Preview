#!/bin/bash

##########################################################
# Modify the variables below in order to make everything #
# work properly. All the softwareupdater keys and the    #
# keystore.txt file should be in the same directory.     #
##########################################################

softwareupdater_server="/path/to/software/server"
base_installer_dir="/path/where/base_installers/will/be/stored"
sofwareupdater_pub_key="/path/to/softwareupdater/pub/key"
softwareupdater_priv_key="/path/to/softwareupdater/priv/key"
version="version_of_seattle_being_released"

# Remove the old tuf server stuff.
rm -rf $softwareupdater_server/*
rm $base_installer_dir/seattle_*
rm -rf $base_installer_dir/geni/monzum_dist/*

# This creates the base installers and copies it over in the appropriate directory
python make_base_installers.py a .. $softwareupdater_pub_key $softwareupdater_priv_key $base_installer_dir $softwareupdater_server $version

chown testgeni $base_installer_dir/seattle_*

ln -s -f $base_installer_dir/seattle_test_linux.tgz $base_installer_dir/seattle_linux.tgz
ln -s -f $base_installer_dir/seattle_test_mac.tgz $base_installer_dir/seattle_mac.tgz
ln -s -f $base_installer_dir/seattle_test_win.zip $base_installer_dir/seattle_win.zip