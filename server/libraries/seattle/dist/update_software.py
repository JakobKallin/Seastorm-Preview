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

import sys
import make_base_installers





DEBUG = False





def update(trunk_location, pubkey, privkey, update_dir):
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

  <Returns>
    None.
  """
  # If we're in DEBUG mode, don't use the real update
  # directory
  if DEBUG:
    print "Debug mode..."
    update_dir = update_dir + "/test"
    
  make_base_installers.prepare_gen_files(trunk_location, update_dir,
                                         False, pubkey, privkey, False)





def main():
  global DEBUG
  
  if len(sys.argv) < 3:
    print "usage: python update_software.py trunk/location/ publickey privatekey updatedir [-d]"
    
  elif len(sys.argv) == 6:
    if sys.argv[5] == "-d":
      DEBUG = True
      
  update(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])





if __name__ == "__main__":
  main()

