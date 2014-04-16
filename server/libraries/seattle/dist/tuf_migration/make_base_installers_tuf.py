"""
<Program Name>
  make_base_installers.py

<Started>
  November 2008
    Revised May 23, 2009
    Revised April 6, 2010

<Author>
  Carter Butaud
    Revised by Zachary Boka

<Purpose>
  Builds the installers for one or more of the supported operating systems,
  depending on options given. Runs on Linux systems only.

  Usage: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ pubkey
          privkey output/dir/ [version of seattle]
          [--wg path/to/Windows/GUI/builder/makensis.exe]
  Flags: m,l,w,i,a,t represent the OS for which the base installer is being
         created.  m = Macintosh, l = Linux, w = Windows, i = Windows Mobile,
         a = all systems. t = include tests in installer.
  NOTE: The Windows GUI installer will ONLY be built if the 'w' or 'a' options
        are passed ALONG WITH the '--wg' option.


  Example of usage on command line:
    python ./Seattle/trunk/dist/make_base_installers.py a ./Seattle/trunk/
     user.publickey user.privatekey ./Installers/ 1.0a

"""

import os
import sys
import glob
import shutil
import zipfile
import tarfile
import tempfile
import subprocess


import clean_folder

# The name of the base directory in each installer.
BASE_INSTALL_DIR = "seattle" 
BASE_PROGRAM_FILES_DIR = "seattle/seattle_repy"
# The base name of each installer = for instance, "seattle_win.zip"
INSTALLER_NAME = "seattle"

# The path to the directory, relative the trunk, of the OS-specific files.
WINDOWS_GUI_PATH = "/dist/win_gui"
WINDOWS_PATH = "/dist/win/scripts"
WINMOB_PATH = "/dist/winmob/scripts"
LINUX_PATH = "/dist/linux/scripts"
MAC_PATH = "/dist/mac/scripts"

# The path to the directory, relative the trunk, of the OS-specific script
# wrappers.
WINDOWS_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/win"
LINUX_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/linux"
MAC_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/mac"

# The path to the Windows GUI builder.
WINDOWS_GUI_BUILDER_PATH = ""



def get_inst_name(dist, version):
  """
  <Purpose>
    Given the OS and the version, returns what the name of the installer
    will be.

  <Arguments>
    dist:
      The OS that the installer is intended for, should be Windows, Macintosh,
      Linux, or Winmob.

    version:

      A string to be appended between the dist and the extension - for
      instance, if version is "0.1d", then the Linux installer name will
      be "seattle_linux0.1d.tgz".

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A string of the installer name for the specified OS and version.
  """

  if version:
    base_name = INSTALLER_NAME + "_" + version + "_" + dist
  else:
    base_name = INSTALLER_NAME + "_" + dist

  if "win" in dist or "Win" in dist or "WIN" in dist:
    if "gui" in dist or "GUI" in dist:
      base_name += ".exe"
    else:
      base_name += ".zip"
  else:    
    base_name += ".tgz"
  return base_name




def check_flags(flags):
  """
  <Purpose>
    Checks that each character in 'flags' is a valid flag and that there is at
    least one valid flag (i.e., m,w,l,i,a).

  <Arguments>
    flags:

      String containing the flags passed in by the user.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    If there is an invalid flag, returns a tuple containing False and the
    offending flag(s). If there is not at least one valid flag, this function
    returns a tuple containing False and the empty strings. Otherwise, if there
    are no problems, a tuple with True and the empty string is returned.
  """

  valid_flags = "mwliat"
  required_flags = "mwlia"
  got_required_flag = False
  no_invalid_flags = True
  badflag = ""

  # Check flags for invalid flags and required flags.
  for char in flags:
    if char not in valid_flags:
      no_invalid_flags = False
      if char not in badflag:
        badflag += char
    elif char in required_flags:
      got_required_flag = True

  # Return results.
  if no_invalid_flags and got_required_flag:
    return (True, badflag)
  else:
    return (False, badflag)




def prepare_gen_files(trunk_location,temp_install_dir,include_tests,pubkey,
                      privkey,finalfiles):
  """
  <Purpose>
    Prepare the general non-installer-specific files (needed for all installers)
    and deposit them into the temporary folder designated to hold the files
    that will be present in the base installer(s), including the metainfo file.

  <Arguments>
    trunk_location:
      The path to the trunk of the repository, used to find all the requisite
      files that appear in the installer.

    pubkey:
      The path to a public key that will be used to generate the metainfo file.

    privkey: 
      The path to a private key that will be used to generate the metainfo file.

    temp_install_dir:
      The temporary directory where the general files to be included in the
      installer will be placed.

    include_tests:
      Boolean variable specifying whether or not to include tests in installer.

    finalfiles:
      Boolean variable specifying whether or not to prepare the final files
      after the metafile has been written


  <Exceptions>
    IOError on bad file paths.    

  <Side Effects>
    All general non-installer-specific files placed into the specified temporary
    installation directory.

  <Returns>
    List of all the files in the temporary installation directory, which will
    be added to the installer tarball.
  """

  # Run preparetest to generate and place all the general installation files
  # in the temporary installation directory.

  # To run /trunk/preparetest.py, we must be in that directory (probably a bug
  # in preparetest.py?)
  original_dir = os.getcwd()
  os.chdir(trunk_location)
  if include_tests:
    p = subprocess.Popen(["python",trunk_location + os.sep + "preparetest.py",
                          "-t",temp_install_dir])
    p.wait()
  else:
    p = subprocess.Popen(["python",trunk_location + os.sep + "preparetest.py",
                          temp_install_dir])
    p.wait()
  os.chdir(original_dir)


  # Copy Anthony Honstain's benchmarking scripts to the installer.
  shutil.copy2(trunk_location + "/resource/benchmark_resources.py", 
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Mac_BSD_resources.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/create_installer_state.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/measuredisk.py", temp_install_dir)
  shutil.copy2(trunk_location + "/resource/vessel.restrictions",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Linux_resources.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/measure_random.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Win_WinCE_resources.py",
               temp_install_dir)

  # Copy the universal installer and uninstaller to the program directory.
  shutil.copy2(trunk_location + "/dist/seattleinstaller.py", temp_install_dir)
  shutil.copy2(trunk_location + "/dist/seattleuninstaller.py", temp_install_dir)

  # Copy the script that stops all running seattle processes.
  shutil.copy2(trunk_location + "/dist/stop_all_seattle_processes.py",
               temp_install_dir)

  # Copy the script that will update old crontab entries on Linux and Darwin
  # systems to the new 2009 seattle crontab entry.  This must remain in the
  # installer indefinitely (or at least for a while) in the event that a user
  # installed seattle with the previous, old crontab entry, then lost permission
  # to modify his crontab.  In the event that he regains permission to modify
  # his crontab, the previously installed crontab entry must be updated.
  shutil.copy2(trunk_location \
                 + "/dist/update_crontab_entry.py", temp_install_dir)

  # Clean the folder of unnecessary files before generating metafile.
  clean_folder.clean_folder(trunk_location + "/dist/initial_files.fi",
                            temp_install_dir)


  # To run writemetainfo.py, we must be in that directory (probably a bug in
  # writemetainfo.py?)
  os.chdir(temp_install_dir)

  # Generate the metainfo file.
  p = subprocess.Popen(["python",temp_install_dir + os.sep + "writemetainfo.py",
                        privkey,pubkey,"-n"])
  p.wait()
  os.chdir(original_dir)


  # If specified, copy remaining files that should not be included in the
  # metafile into the temporary installation directory.
  if finalfiles:
    # Copy the static files to the program directory.
    shutil.copy2(trunk_location + "/dist/nodeman.cfg", temp_install_dir)
    shutil.copy2(trunk_location + "/dist/resources.offcut", temp_install_dir)
    # Run clean_folder a final time to ensure the final directory contains all
    # the necessary files now that the last files have been added.
    clean_folder.clean_folder(trunk_location + "/dist/final_files.fi",
                              temp_install_dir)

  # Copy over the tuf related files.
  shutil.copytree(os.path.join(trunk_location, "tuf"), 
                  os.path.join(temp_install_dir, "tuf"))
  shutil.copytree(os.path.join(trunk_location, "tuf", "simplejson"),
                  os.path.join(temp_install_dir, "simplejson"))

  # This will remove any other unnecessary pyc files that have been 
  # added to the server by accident.
  remove_pyc_files(temp_install_dir)

  return os.listdir(temp_install_dir)







def remove_pyc_files(root_dir):
  """
  Remove all the pyc files in the directory recursively.
  """

  for dirpath, dirnames, filenames in os.walk(root_dir):
    for name in filenames:
      path = os.path.normpath(os.path.join(dirpath, name))
      if os.path.isfile(path) and path.endswith(".pyc"):
        os.remove(path)
  






def package_win_gui(trunk_location, temp_tarball_dir, zip_inst_name,
                    gui_inst_name):
  """
  <Purpose>
    Packages the installation files for Windows into a GUI executable file
    and adds the specific installation scripts for this OS.

    This function extracts the contents of the already-created Windows zipfile
    installer because the zipfile installer contains special Windows files that
    are not located anywhere else in the trunk.

  <Arguments>
    trunk_location:
      The location of the repository trunk.

    temp_tarball_dir:
      The path to the directory in which the installer executable will be
      stored.

    zip_inst_name:
      The name of the Windows zipfile installer.

    gui_inst_name:
      The name that the Windows GUI executable file will have.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final executable in the temporary tarball directory.

  <Returns>
    None.  
   """

  # Create a subdirectory where the GUI installer will be created, and copy all
  # necessary files there.
  win_gui_location = tempfile.mkdtemp()
  shutil.copy(trunk_location + os.sep + WINDOWS_GUI_PATH + os.sep \
                + "seattle_gui_creator.nsi", win_gui_location)

  # Extract the zipfile to the win_gui_location to get all the contents that
  # will be compressed into the Windows gui installer.
  installer_zipfile = zipfile.ZipFile(temp_tarball_dir + os.sep + zip_inst_name,
                                      'r')
  installer_zipfile.extractall(win_gui_location)
  shutil.copy(trunk_location + os.sep + "dist" + os.sep \
                + "extract_custom_info.py",win_gui_location + os.sep \
                + "seattle" + os.sep + "seattle_repy")


  # Change directories to win_gui_location because the Windows gui creator
  # will not work when full file paths are passed in as arguments for some
  # reason.
  original_dir = os.getcwd()
  os.chdir(win_gui_location)

  # Create the Win GUI executable with the Windows GUI builder (makensis.exe)
  # via subprocess.
  gui_creator = subprocess.Popen([WINDOWS_GUI_BUILDER_PATH,
                                  "seattle_gui_creator.nsi"],
                                 stdout=subprocess.PIPE)
  # The communicate() function must be called to prevent the subprocess call
  # above from deadlocking.
  gui_creator.communicate()
  gui_creator.wait()

  # The Windows GUI builder script has a built-in name that it gives to the
  # installer (seattle_win_gui.exe), so rename this file to gui_inst_name.
  os.rename("seattle_win_gui.exe",gui_inst_name)

  # Change back to the original directory.
  os.chdir(original_dir)

  # Put the new GUI installer into the temp_tarball_dir with the other
  # installers.
  shutil.copy(win_gui_location + os.sep + gui_inst_name,temp_tarball_dir)

  # Remove the temporary GUI installer directory.
  shutil.rmtree(win_gui_location)




def package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files):
  """
  <Purpose>
    Packages the installation files for Windows or Windows Mobile into a zipfile
    and adds the specific installation scripts for this OS.

  <Arguments>
    trunk_location:
      The location of the repository trunk.

    temp_install_dir:
      The path to the temporary installation directory.

    temp_tarball_dir:
      The path to the directory in which the installer zipfile(s) is stored.

    inst_name:
      The name that the final installer should have.

    gen_files:
      A list of the general non-installer-specific files located in the
      temporary installer directory.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final zipfile in the temporary tarball directory.

  <Returns>
    None.  
  """

  temp_seattle_dir = tempfile.mkdtemp()
  
  partial_win_zip_path = os.path.join(temp_seattle_dir, inst_name)
  specific_installer_dir = ""


  # We copy over some files, if its not a windows mobile installer
  if "winmob" not in inst_name:
    shutil.copy2(trunk_location + "/dist/win/partial_win.zip", 
                 partial_win_zip_path)

    _extract_zip_file(partial_win_zip_path, temp_seattle_dir)

    specific_installer_dir = trunk_location + WINDOWS_PATH

    # Non-winmob windows need some additional files that needs to be copied over. 
    script_wrappers_dir = trunk_location + WINDOWS_SCRIPT_WRAPPERS_PATH
    _copy_filetree(script_wrappers_dir, os.path.join(temp_seattle_dir, BASE_INSTALL_DIR), 
                   ignore=['svn'])
  else:
    specific_installer_dir = trunk_location + WINMOB_PATH

    

  # Copy over all the general non-os specific files.
  for fname in gen_files:
    source_path = os.path.join(temp_install_dir, fname)
    target_path = os.path.join(temp_seattle_dir,BASE_PROGRAM_FILES_DIR, fname)
    if os.path.isdir(source_path):
      if os.path.exists(target_path):
        shutil.rmtree(target_path)
      shutil.copytree(source_path, target_path)
    else:
      if not os.path.exists(os.path.dirname(target_path)):
        os.makedirs(os.path.dirname(target_path))
      shutil.copy2(source_path, target_path)


  # Copy over all the specific files. Ignoring the files 
  # matching the pattern.
  _copy_filetree(specific_installer_dir, 
                 os.path.join(temp_seattle_dir, BASE_PROGRAM_FILES_DIR), 
                 ignore=['svn', 'LICENSE', 'README', 'manifest.txt'])

  
  # Copy over the License and the Readme file to the top level
  # directory for everyone to read.
  for fname in ['LICENSE.txt', 'README.txt']:
    source_path = os.path.join(specific_installer_dir, fname)
    target_path = os.path.join(temp_seattle_dir, BASE_INSTALL_DIR, fname)
    # Check if the file exists.
    if os.path.exists(source_path):
      shutil.copy2(source_path, target_path)

  
  # Create the archive zip file.
  _archive_zip_file(os.path.join(temp_tarball_dir, inst_name), 
                    os.path.join(temp_seattle_dir, BASE_INSTALL_DIR))

  # Remove the temporary directory.
  shutil.rmtree(temp_seattle_dir)






def package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files):
  """
  <Purpose>
    Packages the installation files specific to Linux or Macintosh into a
    tarball and adds the specific installation scripts for this OS.

  <Arguments>
    trunk_location:
      The location of the repository trunk.

    temp_install_dir:
      The path to the temporary installation directory.

    temp_tarball_dir:
      The path to the directory in which the installer tarball(s) is stored.

    inst_name:
      The name that the final installer should have.

    gen_files:
      A list of the general non-installer-specific files located in the
      temporary installer directory.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """

  installer_tarfile = tarfile.open(temp_tarball_dir + os.sep + inst_name,"w:gz")
    
  # Put all general installer files into the tar file.
  for fname in gen_files:
    installer_tarfile.add(temp_install_dir + os.sep + fname,
                          os.path.join(BASE_PROGRAM_FILES_DIR, fname), recursive=True)



  # Put all Linux- and Mac-specific files in to tarball.


  # First, copy all scripts that belong in BASE_PROGRAM_FILES_DIR.
  if "linux" in inst_name:
    specific_installer_dir = trunk_location + os.sep + LINUX_PATH
  else:
    specific_installer_dir = trunk_location + os.sep + MAC_PATH
  specific_files = os.listdir(specific_installer_dir)

  # Add the OS-specific files to the tarfile.
  for fname in specific_files:
    if not "svn" in fname and fname != "manifest.txt":
      if "README" in fname or "LICENSE" in fname:
        installer_tarfile.add(specific_installer_dir + os.sep + fname,
                              BASE_INSTALL_DIR + os.sep + fname,False)
      else:
        installer_tarfile.add(specific_installer_dir + os.sep + fname,
                              BASE_PROGRAM_FILES_DIR + os.sep + fname,False)



  # Second, copy all script wrappers (which call those in the
  # BASE_PROGRAM_FILES_DIR) to the BASE_INSTALL_DIR.
  if "linux" in inst_name:
    script_wrappers_dir = trunk_location + os.sep + LINUX_SCRIPT_WRAPPERS_PATH
  else:
    script_wrappers_dir = trunk_location + os.sep + MAC_SCRIPT_WRAPPERS_PATH
  script_wrappers = os.listdir(script_wrappers_dir)

  # Add script wrappers to the zipfile.
  for fname in script_wrappers:
    if not "svn" in fname:
      installer_tarfile.add(script_wrappers_dir + os.sep + fname,
                            BASE_INSTALL_DIR + os.sep + fname,False)


  installer_tarfile.close()





def create_softwareupdater_server(temp_install_dir, update_server_dir, keystore_location):
  """
  <Purpose>
    We create and prepare the software updater server. It calls quickstart
    in order to properly prepare the server.

  <Arguments>
    temp_install_dir - The directory where all the general non-os specific
      files are stored for the moment.

    update_server_dir - The root dir where the sofware updater server
      resides.

    keystore_location - where to store the keys generated by tuf preparation.

  <Side_Effects>
    Calls quickstart with subprocess

  <Error>
    Error will be raised if the server directory has already been prepared.

  <Return>
    Returns the list of file in the temp_install_dir
  """

  os.chmod(temp_install_dir, 0755)
  
  
  # These are the arguments used to create the softwareupdater
  # server. We run quickstart, which takes care of most of these.
  args = ["python",
          "quickstart.py",
          "-k",
          keystore_location+"/keystore.txt",
          "-t",
          "1",
          "-l",
          update_server_dir,
          "-r",
          temp_install_dir,
          "-e",
          "12/12/2012"]
  retcode = subprocess.call(args)
  
  # Make sure we ran quickstart successfully.
  if retcode:
    raise Exception("Unable to run quickstart.py: " + str(retcode))
        

  return os.listdir(temp_install_dir)






def copy_softwareupdater_files(temp_install_dir, update_server_dir):
  """
  This function copies over the directory structure
  that is needed for the softwareupdater to run 
  properly.
  """

  # Create the necessary directories and copy over the all the
  # necessary files.
  os.makedirs(os.path.join(temp_install_dir, "repo", "cur"))
  os.makedirs(os.path.join(temp_install_dir, "repo", "prev"))

  for f in glob.iglob(os.path.join(update_server_dir, "meta/", "*")):
    shutil.copy(f, os.path.join(temp_install_dir, "repo", "cur"))

  for f in glob.iglob(os.path.join(update_server_dir, "meta/", "*")):
    shutil.copy(f, os.path.join(temp_install_dir, "repo", "prev"))


  return os.listdir(temp_install_dir)







def update_softwareupdater_server(temp_install_dir, update_server_dir, keystore_location):
  """
  <Purpose>
    We update the sofware updater server, in order to push the new updates
    onto the seattle clients.

  <Arguments>
    temp_install_dir - The directory where all the general non-os specific
      files are stored for the moment.

    update_server_dir - The root dir where the sofware updater server 
      resides.

    keystore_location - where to store the keys generated by tuf preparation.

  <Side_Effects>
    Calls quickstart with subprocess

  <Error>
    Error will be raised if the server directory has already been prepared.

  <Return>
    None
  """


  # The path to the configuration file.
  cfg_path = os.path.join(update_server_dir, 'root.cfg')

  # Make sure we have the right permissions on all files.
  os.chmod(temp_install_dir, 0755)
  args = ["python",
          "quickstart.py",
          "-u",
          "-k",
          keystore_location+"/keystore.txt",
          "-l",
          update_server_dir,
          "-r",
          temp_install_dir,
          "-c",
          cfg_path]

  # Update the sofwareupdater server from the temp_install dir.
  retcode = subprocess.call(args)

  # Make sure we ran quickstart successfully.
  if retcode:
    raise Exception("Unable to run quickstart.py: " + str(retcode))




def test_arguments(arguments):
  """
  """
  # Test argument flags
  if len(arguments) < 7:
    print "Too few arguments."
    return False
  elif len(arguments) > 10:
    print "Too many arguments."
    return False


  flags = arguments[1]
  passed, offenses = check_flags(flags)
  if not passed:
    if offenses == "":
      print "Requires at least one of these flags: m,l,w,i,a"
    else:
      print "Invalid flag(s): " + offenses
    return False


  # Test argument paths, and get their absolute paths.
  # Test trunk path.
  if not os.path.exists(arguments[2]):
    raise IOError("Trunk not found at " + arguments[2])

  # Test output directory path.
  if not os.path.exists(sys.argv[5]):
    raise IOError("Output directory does not exist.")

  # Test public key path.
  if not os.path.exists(sys.argv[3]):
    raise IOError("Public key not found.")

  # Test private key path.
  if not os.path.exists(sys.argv[4]):
    raise IOError("Private key not found.")

  if not os.path.exists(sys.argv[6]):
    raise IOError("Softwareupdater server directory does not exist.")

  server_dir_list = os.listdir(sys.argv[6])
  if len(server_dir_list) == 0:
    raise IOError("Softwareupdater server has not been created yet!")

  for file_name in ["targets", "meta", "root.cfg"]:
    if file_name not in server_dir_list:
      raise IOError("Softwareupdater server seems to be not exist or" +
                    " malformed. Please check the path: " + sys.argv[6]) 


  # All arguments are valid.
  return True



def _extract_zip_file(zip_file_name, output_path_dir=os.getcwd()):
  """
  Given a zip file name, extract all the files in the zip
  file to the provided path, or the current directory if
  no path is provided.
  """

  # If directories for the archive dir does not
  # exist, then create them.
  if not os.path.exists(output_path_dir):
    os.makedirs(output_path_dir)

  # Get reference to the zip file.
  zip_fd = zipfile.ZipFile(zip_file_name)

  # Get a list of all the files in the zilp file.
  file_list = zip_fd.namelist()

  # Open each file up in the zip file, and write it
  # as a regular file.
  for filemember in file_list:
    
    # Make sure that the filemember is a zipinfo object.
    if not isinstance(filemember, zipfile.ZipInfo):
      filemember = zip_fd.getinfo(filemember)

    filename = filemember.filename
    # Normalize the file path and get the file name out of the zipinfo object.
    targetpath = os.path.normpath(os.path.join(output_path_dir, filename))

    # If the filename is a directory path, then we create the directory
    # if it does not exist, otherwise we continue.
    if filename[-1] == '/':
      if not os.path.isdir(targetpath):
        os.makedirs(targetpath)
      continue

    source = zip_fd.read(filename)
    target = open(targetpath, 'wb')
    target.write(source)
    target.close()

  zip_fd.close()






def _archive_zip_file(zip_filename, root_dir=os.getcwd(), append=False):
  """
  Create a zip file recursively given a root_dir from
  where to create the zip file from. Most of this code
  has been copied over from shutil.mak_archive implemented
  in Python 2.7 with modification to simply it. The reason 
  for this function is because we support Python 2.5.4 
  but Python 2.5.4 does not have any methods that does this.
  """

  # Get the directory path for archive.
  archive_dir = os.path.dirname(zip_filename)

  # If directories for the archive dir does not
  # exist, then create them.
  if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

  # Open up a zip file to create or open up an existing one.
  if append:
    zip = zipfile.ZipFile(zip_filename, "a",
                          compression=zipfile.ZIP_DEFLATED)
  else:
    zip = zipfile.ZipFile(zip_filename, "w",
                          compression=zipfile.ZIP_DEFLATED)

  # We want to create the zip file from the directory its in, otherwise
  # the whole tree of directories are created.
  cur_dir = os.getcwd()
  archive_root = os.path.dirname(root_dir)
  os.chdir(archive_root)
  archive_base = os.path.basename(root_dir)

  # Recursively add all the files into the zip file.
  for dirpath, dirnames, filenames in os.walk(archive_base):
    for name in filenames:
      path = os.path.normpath(os.path.join(dirpath, name))
      if os.path.isfile(path):
        zip.write(path, path)

  # Close the zip file.
  zip.close()
  
  # Change directory back
  os.chdir(cur_dir)


def _contains_forbidden_substring(name, forbidden):
  """
  Check if name contains any of the words in forbidden list
  """
  return any(prohibit_name in name for prohibit_name in forbidden)

  
def _copy_filetree(source_dir, target_dir, ignore=[]):
  """
  Given a source directory and target directory, recursively 
  copy all the files in the source directory to the target 
  directory. If the target directory does not exist, create 
  it. If the file name is in the ignore list we don't copy 
  it over. Most of the code was copied over from Python 2.7
  implementation. The reason for this is because it was not
  implemented in Python 2.5.4, which we support.
  """


  # Create the target directory if not there.
  if not os.path.exists(target_dir):
    os.makedirs(target_dir)

  for file_name in os.listdir(source_dir):
    
    # If file name in ignore list, then we continue.
    if _contains_forbidden_substring(file_name, ignore):
      continue
  
    source_path = os.path.join(source_dir, file_name)
    target_path = os.path.join(target_dir, file_name)

    # Recursively copy directories.
    if os.path.isdir(source_path):
      _copy_filetree(source_path, target_path, ignore)
    else:
      # Copy over the files.
      shutil.copy2(source_path, target_path)






def usage():
  print "USAGE: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ " \
      + "pubkey privkey output/dir/ softwareupdater_dir [version of seattle] " \
      + "[--wg path/to/Windows/GUI/builder/makensis.exe]"
  print "\tFLAGS: m,l,w,i,a,t represent the OS for which the base installer " \
      + "is being created.  m = Macintosh, l = Linux, w = Windows, " \
      + "i = Windows Mobile, a = all systems. t = include tests in installer."
  print "\tNOTE: The Windows GUI installer will ONLY be built if the 'w' or " \
      + "'a' options are passed ALONG WITH the '--wg' option."


def main():

  # Prepare to create installer(s).

  # Test arguments and find full pathnames.
  arguments_valid = test_arguments(sys.argv)
  if not arguments_valid:
    usage()
    return

  # Reaching this point means all arguments are valid, so set the variables and
  # get full pathnames when necessary.
  # NOTE: IF MORE OPTIONS ARE EVER ADDED TO THIS PROGRAM, CONSIDER USING THE
  #       PYTHON MODULE getopt TO PARSE THE OPTIONS SINCE THE BELOW LOGIC WILL
  #       START TO GET REALLY COMPLICATED.
  installer_type = sys.argv[1]
  trunk_location = os.path.realpath(sys.argv[2])
  output_dir = os.path.realpath(sys.argv[5])
  pubkey = os.path.realpath(sys.argv[3])
  privkey = os.path.realpath(sys.argv[4])
  softwareupdater_server_dir = os.path.realpath(sys.argv[6])
  version = ""
  
  # Figure out if the optional version number or the path to the Windows GUI
  # builder was passed in.
  if len(sys.argv) > 7:
    if len(sys.argv) == 8:
      # Only one extra option was passed, so it must be the version number.
      version = sys.argv[7]
      if version == "--wg":
        print "Windows GUI builder path not specified"
        usage()
        return

    else:
      global WINDOWS_GUI_BUILDER_PATH

      if sys.argv[7] == "--wg":
        # The path to the Windows GUI builder was passed in.
        if len(sys.argv) == 8:
          # The path was not given with the "--wg" option.
          usage()
          return
        elif len(sys.argv) > 9:
          # The version number was also given.
          version = sys.argv[8]

        WINDOWS_GUI_BUILDER_PATH = sys.argv[8]


      else:
        # The version must have been given before the path to the Windows GUI
        # builder if the path was given at all.
        version = sys.argv[7]
        if sys.argv[8] != "--wg":
          # An extraneous option must have been given.
          usage()
          return
        else:
          WINDOWS_GUI_BUILDER_PATH = sys.argv[9]

  if WINDOWS_GUI_BUILDER_PATH:
    # Confirm that the path exists.
    if not os.path.lexists(WINDOWS_GUI_BUILDER_PATH):
      print "Invalid path to the Windows GUI builder: ",
      print WINDOWS_GUI_BUILDER_PATH
      print "Failed to build installers."
      return
    else:
      # Get full file path.
      WINDOWS_GUI_BUILDER_PATH = os.path.realpath(WINDOWS_GUI_BUILDER_PATH)






  # Begin creating base installers.
  print "Creating installer(s) - this may take a few moments...."

  # Create temporary directory for the files to go into the installer.
  temp_install_dir = tempfile.mkdtemp()
  # Create temporary directory for creating the tarball(s) / zipfile(s).
  temp_tarball_dir = tempfile.mkdtemp()


  # Prepare all general non-installer-specific files to go into installer.
  print "Preparing all general non-OS-specific files...."
  include_tests = False
  if "t" in installer_type:
      include_tests = True
  prepare_gen_files(trunk_location,temp_install_dir,include_tests,
                    pubkey,privkey,True)

  gen_files = copy_softwareupdater_files(temp_install_dir, softwareupdater_server_dir)


  print "Complete."


  # Build individual installer(s).
  print "Customizing installer(s) for the specified operating system(s)...."
  created_installers = []

  # Package the Windows installer.
  if "w" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("win", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files)
    created_installers.append(inst_name)

    # See if we need to create the Windows GUI installer
    if WINDOWS_GUI_BUILDER_PATH:
      inst_name_gui = get_inst_name("win_gui", version)
      package_win_gui(trunk_location, temp_tarball_dir, inst_name,
                      inst_name_gui)
      created_installers.append(inst_name_gui)


  # Package the Linux installer.
  if "l" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("linux", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files)
    created_installers.append(inst_name)


  # Package the Mac installer.
  if "m" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("mac", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files)
    created_installers.append(inst_name)


  # Package the Windows Mobile installer.
  if "i" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("winmob", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files)
    created_installers.append(inst_name)



  # Move the installer tarball(s) / zipfile(s)  to the specified output
  # directory.
  for tarball in os.listdir(temp_tarball_dir):
    shutil.copy2(temp_tarball_dir + os.sep + tarball, output_dir)

  # Remove the temporary directories
  
  shutil.rmtree(temp_install_dir)
  shutil.rmtree(temp_tarball_dir)

  print
  print "Finished." 
  print
  print "The following base installers have been placed in " + output_dir + ":"
  for installer in created_installers:
      print installer




if __name__ == "__main__":
    main()
