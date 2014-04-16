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
  Flags: m,l,w,i,a,d,t represent the OS for which the base installer is being
         created.  m = Macintosh, l = Linux, w = Windows, i = Windows Mobile,
         d = Android, a = all systems. t = include tests in installer.
  NOTE: The Windows GUI installer will ONLY be built if the 'w' or 'a' options
        are passed ALONG WITH the '--wg' option.


  Example of usage on command line:
    python ./Seattle/trunk/dist/make_base_installers.py a ./Seattle/trunk/
     user.publickey user.privatekey ./Installers/ 1.0a

"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
import tarfile

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
      Linux, Winmob, or Android.

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
  elif "android" in dist:
    base_name += ".zip"
  else:
    base_name += ".tgz"
  return base_name




def check_flags(flags):
  """
  <Purpose>
    Checks that each character in 'flags' is a valid flag and that there is at
    least one valid flag (i.e., m,w,l,i,d,a).

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

  valid_flags = "mwlidat"
  required_flags = "mwliad"
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


  return os.listdir(temp_install_dir)




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
                                      'r', zipfile.ZIP_DEFLATED)
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

  # Open the Windows zipfile for writing, or create a zipfile for Windows
  # Mobile.
  if not "winmob" in inst_name:
    shutil.copy2(trunk_location + "/dist/win/partial_win.zip",
                 temp_tarball_dir + os.sep + inst_name)
    installer_zipfile = zipfile.ZipFile(temp_tarball_dir + os.sep + inst_name,
                                        "a", zipfile.ZIP_DEFLATED)
  else:
    installer_zipfile = zipfile.ZipFile(temp_tarball_dir + os.sep + inst_name,
                                        "w", zipfile.ZIP_DEFLATED)

  # Put all general program files into zipfile.
  for fname in gen_files:
    if os.path.isdir(temp_install_dir + os.sep + fname):
      write_files_in_dir_to_zipfile(temp_install_dir + os.sep + fname, 
                            BASE_PROGRAM_FILES_DIR + os.sep + fname + os.sep, 
                            installer_zipfile)
    else:
      installer_zipfile.write(temp_install_dir + os.sep + fname,
                            BASE_PROGRAM_FILES_DIR + os.sep + fname)



  # Put all files specific to this installer into zipfile.

  # First, copy all scripts that belong in the BASE_PROGRAM_FILES_DIR.
  if not "winmob" in inst_name:
    specific_installer_dir = trunk_location + os.sep + WINDOWS_PATH
  else:
    specific_installer_dir = trunk_location + os.sep + WINMOB_PATH
  specific_files = os.listdir(specific_installer_dir)

  # Add OS-specific files to the zipfile.
  for fname in specific_files:
    if not "svn" in fname and fname != "manifest.txt":
      # Add the README and LICENSE files to the highest-level directory
      # (BASE_INSTALL_DIR).
      if "LICENSE" in fname or "README" in fname:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                                BASE_INSTALL_DIR + os.sep + fname)
      else:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                              BASE_PROGRAM_FILES_DIR + os.sep + fname)



  # Second, copy all script wrappers (which call those in the
  # BASE_PROGRAM_FILES_DIR) to the BASE_INSTALL_DIR.
  if "winmob" in inst_name:
    return
  else:
    script_wrappers_dir = trunk_location + os.sep + WINDOWS_SCRIPT_WRAPPERS_PATH
  script_wrappers = os.listdir(script_wrappers_dir)

  # Add script wrappers to the zipfile.
  for fname in script_wrappers:
    if not "svn" in fname:
      installer_zipfile.write(script_wrappers_dir + os.sep + fname,
                              BASE_INSTALL_DIR + os.sep + fname)


  installer_zipfile.close()
    


def write_files_in_dir_to_zipfile(sourcepath, arcpath, zipfile):
  '''
  <Purpose>
    Inserts the files in the current directory into the specified zipfile.
  <Arguments>
    sourcepath:
      The source path of the files to add.
    arcpath:
      The zip file's internal destination path to write to.
    zipfile:
      The zip file to write to.
    files:
      If specified, only these files are copied. Only files in the immediate
      directory can be specified.
    skipfiles:
      If specified, these files will be skipped. Only files in the immediate 
      directory can be skipped.
  <Side Effects>
    Copies the files that are in sourcepath to arcpath in the zipfile. If files
    is specified, then only those files are copied.
  <Exceptions>
    None
  <Return>
    None
  '''
  files = os.listdir(sourcepath)

  for fname in files:
    sourcefilepath = sourcepath + os.sep + fname
    targetfilepath = arcpath + os.sep + fname
    if os.path.isfile(sourcefilepath):
      zipfile.write(sourcefilepath, targetfilepath)
    else:
      write_files_in_dir_to_zipfile(sourcefilepath, targetfilepath, zipfile)

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
    if fname not in ['pyreadline']:
      installer_tarfile.add(temp_install_dir + os.sep + fname,
                          BASE_PROGRAM_FILES_DIR + os.sep + fname,True)



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





def package_android(trunk_location, temp_install_dir, temp_tarball_dir,
                    inst_name, gen_files):
  """
  <Purpose>
    Packages the installation files specific to Android into a
    tarball and adds the specific installation scripts for this OS.
    THIS IS CUT AND PASTED FROM ABOVE WITH ONLY MINOR CHANGES.  NEEDS REFACTOR!

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

  installer_zipfile = zipfile.ZipFile(temp_tarball_dir+os.sep+inst_name, "w", zipfile.ZIP_DEFLATED)
    
  # Put all general program files into zipfile.
  for fname in gen_files:
    if os.path.isdir(temp_install_dir + os.sep + fname):
      if fname not in ['pyreadline']:
        write_files_in_dir_to_zipfile(temp_install_dir + os.sep + fname, 
                            BASE_PROGRAM_FILES_DIR + os.sep + fname + os.sep, 
                            installer_zipfile)
    else:
      installer_zipfile.write(temp_install_dir + os.sep + fname,
                            BASE_PROGRAM_FILES_DIR + os.sep + fname)


  # Put generic files in the zipfile.  (Same as Linux)
  specific_installer_dir = trunk_location + os.sep + LINUX_PATH
  specific_files = os.listdir(specific_installer_dir)

  # Add the OS-specific files to the zipfile.
  for fname in specific_files:
    if not "svn" in fname and fname != "manifest.txt":
      if "README" in fname or "LICENSE" in fname:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                              BASE_INSTALL_DIR + os.sep + fname)
      else:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                              BASE_PROGRAM_FILES_DIR + os.sep + fname)



  # Second, copy all script wrappers (which call those in the
  # BASE_PROGRAM_FILES_DIR) to the BASE_INSTALL_DIR.
  script_wrappers_dir = trunk_location + os.sep + LINUX_SCRIPT_WRAPPERS_PATH
  script_wrappers = os.listdir(script_wrappers_dir)

  # Add script wrappers to the zipfile.
  for fname in script_wrappers:
    if not "svn" in fname:
      installer_zipfile.write(script_wrappers_dir + os.sep + fname, BASE_INSTALL_DIR + os.sep + fname)


  installer_zipfile.close()







def test_arguments(arguments):
  """
  """
  # Test argument flags
  if len(arguments) < 6:
    print "Too few arguments."
    return False
  elif len(arguments) > 9:
    print "Too many arguments."
    return False


  flags = arguments[1]
  passed, offenses = check_flags(flags)
  if not passed:
    if offenses == "":
      print "Requires at least one of these flags: m,l,w,i,d,a"
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



  # All arguments are valid.
  return True




def usage():
  print "USAGE: python make_base_installer.py m|l|w|i|d|a|t path/to/trunk/ " \
      + "pubkey privkey output/dir/ [version of seattle] " \
      + "[--wg path/to/Windows/GUI/builder/makensis.exe]"
  print "\tFLAGS: m,l,w,i,d,a,t represent the OS for which the base installer " \
      + "is being created.  m = Macintosh, l = Linux, w = Windows, " \
      + "i = Windows Mobile, d = Android, a = all systems. t = include tests in installer."
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
  version = ""
  # Figure out if the optional version number or the path to the Windows GUI
  # builder was passed in.
  if len(sys.argv) > 6:
    if len(sys.argv) == 7:
      # Only one extra option was passed, so it must be the version number.
      version = sys.argv[6]
      if version == "--wg":
        print "Windows GUI builder path not specified"
        usage()
        return

    else:
      global WINDOWS_GUI_BUILDER_PATH

      if sys.argv[6] == "--wg":
        # The path to the Windows GUI builder was passed in.
        if len(sys.argv) == 7:
          # The path was not given with the "--wg" option.
          usage()
          return
        elif len(sys.argv) > 8:
          # The version number was also given.
          version = sys.argv[8]

        WINDOWS_GUI_BUILDER_PATH = sys.argv[7]


      else:
        # The version must have been given before the path to the Windows GUI
        # builder if the path was given at all.
        version = sys.argv[6]
        if sys.argv[7] != "--wg":
          # An extraneous option must have been given.
          usage()
          return
        else:
          WINDOWS_GUI_BUILDER_PATH = sys.argv[8]

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
  gen_files = prepare_gen_files(trunk_location,temp_install_dir,include_tests,
                                pubkey,privkey,True)
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

  # Package the Android installer.
  if "d" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("android", version)
    package_android(trunk_location, temp_install_dir, temp_tarball_dir,
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
