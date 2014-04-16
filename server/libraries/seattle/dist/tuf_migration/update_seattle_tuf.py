"""
<Program Name>
  update_software.py

<Started>
  December 1, 2008

<Author>
  Carter Butaud

<Purpose>
  Populates the folder that the software updater checks with
  the latest version of the code.
"""

import os
import sys
import shutil
import tempfile
import make_base_installers





DEBUG = False





def update(trunk_location, pubkey, privkey, keystore_location, update_dir):
  """
  <Purpose>
    Populates the update directory (set by a constant) with the
    program files from the current repository.
  
  <Arguments>
    trunk_location:
      The location of the repository's trunk directory, used to
      find the program files.

    pubkey:
      The public key used to generate the metafile.

    privkey:
      The private key used to generate the metafile.
    
    updatedir:
      The directory to put the generated update files in.
    
  <Exceptions>
    IOError on bad filepath.
  
  <Side Effects>
    None.
"Melody Kadenko" <melody@cs.washington.edu>, 
  <Returns>
    None.
  """
  # If we're in DEBUG mode, don't use the real update
  # directory
  if DEBUG:
    print "Debug mode..."
    update_dir = update_dir + "/test"
  
  # Create temporary directory for the files to go into the installer.
  temp_install_dir = tempfile.mkdtemp()

  try:
    make_base_installers.prepare_gen_files(trunk_location, temp_install_dir,
                                           False, pubkey, privkey, False)


    shutil.copy2(os.path.join(temp_install_dir, "metainfo"), "/home/testgeni/temp/metainfo_update")
    # Update the softwareupdater server directory with the files.
    make_base_installers.update_softwareupdater_server(temp_install_dir, update_dir,
                                                      keystore_location)
  finally:
    # Remove the temporary folder
    shutil.rmtree(temp_install_dir)
    





def main():
  global DEBUG
  
  if len(sys.argv) < 6:
    print "usage: python update_software.py trunk/location/ publickey privatekey keystore updatedir [-d]"
    exit()
    
  elif len(sys.argv) == 6:
    if sys.argv[5] == "-d":
      DEBUG = True

  trunk_location = os.path.realpath(sys.argv[1])
  pubkey = os.path.realpath(sys.argv[2])
  privkey = os.path.realpath(sys.argv[3])
  keystore = os.path.realpath(sys.argv[4])
  updatedir = os.path.realpath(sys.argv[5])

  update(trunk_location, pubkey, privkey, keystore, updatedir)





if __name__ == "__main__":
  main()

