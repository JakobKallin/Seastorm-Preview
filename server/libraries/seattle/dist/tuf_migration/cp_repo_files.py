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
import make_base_installers



def main():
  global DEBUG
  
  if len(sys.argv) < 2:
    print "usage: python cp_repo_files.py dest_dir software_server_dir "
    exit()
    
  dest_dir = os.path.realpath(sys.argv[1])
  softwareupdater_server_dir = os.path.realpath(sys.argv[2])

  make_base_installers.copy_softwareupdater_files(dest_dir, softwareupdater_server_dir)



if __name__ == "__main__":
  main()

