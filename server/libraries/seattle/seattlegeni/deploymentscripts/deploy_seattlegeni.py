"""
<Program Name>
  deploy_seattlegeni.py

<Started>
  July 29, 2009

<Author>
  Justin Samuel

<Purpose>
  Deploys all components of seattlegeni. Some things (e.g. database setup,
  config file modification to enter db user/pass info, etc.) still need
  to be done after this is run. See the instructions in:
  seattlegeni/README.txt

<Description>
  The script backs up the target deploy directory if it exists and the user
  wants to proceed. It then deploys all required files to the deploy
  directory the user specified.

<Usage>
  python deploy_seattlegeni.py <path/to/svn/trunk> <dir/to/deploy/to>
  
"""

import glob
import os
import shutil
import subprocess
import sys
import time





# This function was taken from preparetest. It seemed annoying to depend on
# preparetest just for this. If we use preparetest for anything else later on,
# (e.g. preparing tests?), then we should remove this.
def _copy_to_target(file_expr, target):
  """
  file_expr may contain wildcards
  target must specify an existing directory with no wildcards
  """
  files_to_copy = glob.glob(file_expr)
  for file_path in files_to_copy:
    if os.path.isfile(file_path):
      shutil.copyfile(file_path, target + "/" + os.path.basename(file_path))





def _print_post_deploy_instructions():
  print
  print "Deployed successfully. The file trunk/seattlegeni/README.txt contains the"
  print "rest of the info you'll need to get things running."





def _deploy_seattle_files_to_directory(trunkdir, targetdir):
  """
  Deploys a copy of all seattle files needed to run repy code to a specified
  directory.
  """
  
  print "Deploying seattle and repy library code to " + targetdir
  
  # Copy the repy files needed by various parts of seattlegeni,
  # including ones we don't use but may be required to import repyhelper 
  # (OBSOLETE?).
  _copy_to_target(os.path.join(trunkdir, "repy", "*"), targetdir)
  _copy_to_target(os.path.join(trunkdir, "nodemanager", "*"), targetdir)
  _copy_to_target(os.path.join(trunkdir, "portability", "*"), targetdir)
  _copy_to_target(os.path.join(trunkdir, "seattlelib", "*"), targetdir)

  _process_mix_files_in_directory(trunkdir, targetdir)





#iterate through the .mix files in current folder and run them through the preprocessor
#script_path must specify the name of the preprocessor script
#the working directory must be set to the directory containing the preprocessor script prior to executing this function.
def _process_mix_files_in_directory(trunkdir, directory_with_mix_files):
 
  originaldir = os.getcwd()
  os.chdir(directory_with_mix_files)

  mix_files = glob.glob("*.mix")
 
  # Generate a .py file for each .mix file.
  for file_path in mix_files:
    processed_file_path = (os.path.basename(file_path)).replace(".mix", ".py")
    retval = subprocess.call(["python", "repypp.py", file_path, processed_file_path])
    if retval != 0:
      exit_with_message(1, "Failed converting " + file_path + " to " + processed_file_path)

  os.chdir(originaldir)





def main():
    
  if not len(sys.argv) == 3:
    exit_with_message(2, "Usage: python deploy_seattlegeni.py <path/to/svn/trunk> <dir/to/deploy/to>")
  
  trunkdir = sys.argv[1]
  deployroot = sys.argv[2]
  
  if not os.path.isdir(trunkdir):
    exit_with_message(1, "ERROR: the provided path to the svn trunk does not exist.")

  if not os.path.exists(os.path.join(trunkdir, "seattlegeni")):
    exit_with_message(1, "ERROR: the given svn trunk directory doesn't contains a seattlegeni directory.")

  # Warn the user if the provided deploy directory exists and if it should be replaced.
  # We actually rename rather than remove the old one, just to be paranoid.
  replace_deployment_dir = False
  if os.path.isdir(deployroot):
    print "WARNING: existing directory found at directory to deploy: " + deployroot
    ans = raw_input("Backup and replace this directory (copying config files to the new deployment)? [y/n]")
    replace_deployment_dir = str.lower(ans) == 'y'
    if not replace_deployment_dir:
      exit_with_message(2, "You chose not to replace the directory.")
    else:
      print
      renameddir = deployroot.rstrip('/').rstrip('\\') + '.bak.' + str(time.time())
      print "Renaming existing directory " + deployroot + " to " + renameddir
      shutil.move(deployroot, renameddir)

  # Create the directory we will deploy to.
  print "Creating directory " + deployroot
  os.mkdir(deployroot)

  # Copy over the seattlegeni files from svn to the deploy directory.
  #seattlegeni_svn = os.path.join(trunkdir, "seattlegeni", "website")
  seattlegeni_svn_dir = os.path.join(trunkdir, "seattlegeni")
  seattlegeni_deploy_dir = os.path.join(deployroot, "seattlegeni")
  print "Copying " + seattlegeni_svn_dir + " to " + seattlegeni_deploy_dir
  shutil.copytree(seattlegeni_svn_dir, seattlegeni_deploy_dir, symlinks=True)

  # Deploy the seattle/repy library files in a directory called "seattle". This
  # will serve. This will be the sole location of repy files in seattlegeni and
  # will also serve as a python package called "seattle" for use within
  # seattlegeni code.
  seattle_package_dir = os.path.join(deployroot, "seattle")
  os.mkdir(seattle_package_dir)
  # Open/close file to emulate a "touch __init__.py"
  open(os.path.join(seattle_package_dir, "__init__.py"), "a").close()
  _deploy_seattle_files_to_directory(trunkdir, seattle_package_dir)
  
  # If we replaced an existing directory, then copy the config files from the
  # old deployment to the new one.
  if replace_deployment_dir:
    # The website settings files.
    old_settings_path = os.path.join(renameddir, "seattlegeni", "website", "settings.py")
    new_settings_path = os.path.join(seattlegeni_deploy_dir, "website", "settings.py")
    print "Copying " + old_settings_path + " to " + new_settings_path
    # Use copy2 to preserve permissions, e.g. in case these weren't world-readable.
    shutil.copy2(old_settings_path, new_settings_path)
    
    # The keydb config file.
    old_keydb_config_path = os.path.join(renameddir, "seattlegeni", "keydb", "config.py")
    new_keydb_config_path = os.path.join(seattlegeni_deploy_dir, "keydb", "config.py")
    print "Copying " + old_keydb_config_path + " to " + new_keydb_config_path
    # Use copy2 to preserve permissions, e.g. in case these weren't world-readable.
    shutil.copy2(old_keydb_config_path, new_keydb_config_path)

    # The backend config file.
    old_keydb_config_path = os.path.join(renameddir, "seattlegeni", "backend", "config.py")
    new_keydb_config_path = os.path.join(seattlegeni_deploy_dir, "backend", "config.py")
    print "Copying " + old_keydb_config_path + " to " + new_keydb_config_path
    # Use copy2 to preserve permissions, e.g. in case these weren't world-readable.
    shutil.copy2(old_keydb_config_path, new_keydb_config_path)

  state_key_path = os.path.join(seattlegeni_deploy_dir, "node_state_transitions", "statekeys")
  beta_state_key_path = os.path.join(seattlegeni_deploy_dir, "node_state_transitions", "statekeys_beta")
  
  # Remove the production key from the deployment, as we don't want anyone to get confused by them.
  # If there is any error, just ignore it.
  try:
    shutil.rmtree(state_key_path, ignore_errors=True)
    shutil.rmtree(beta_state_key_path, ignore_errors=True)
  except:
    pass

  _print_post_deploy_instructions()





def exit_with_message(retval, message):
  print message
  print "Exiting."
  sys.exit(retval)





if __name__ == '__main__':
  main()
