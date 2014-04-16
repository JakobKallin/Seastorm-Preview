"""
<Author>
  Cosmin Barsan
  
  Edited to add an optional argument to also copy the repy tests by 
  Brent Couvrette on November 13, 2008.

  Conrad Meyer, Thu Nov 26 2009: Move dynamic ports code from run_tests.py
  to preparetest.py.

  Moshe Kaplan, 2012-03-14: Merge in changes from modified repyv1 and minor
  cleanup.

<Start Date>
  October 3, 2008

<Description>
  This script was adapted from the bash script preparetest. This script first
  erases all the files in a target directory and then copies the necessary 
  files to run repy into it. Afterwards, the .mix files in the target directory
  are ran through the preprocessor.  The target directory that is passed to the
  script must exist.

<Usage>
  preparetest.py  [-t]  [-v] [-c] [-r] <target_directory>

    -t or --testfiles copies in all the files required to run the unit tests
    -v or --verbose displays significantly more output on failure to processa mix file
    -c or --checkapi copies the checkapi source files
    -r or --randomports replaces the default ports of 12345, 12346, and 12347
                        with three random ports between 52000 and 53000. 

<Example>
  Using preparetest to prepare and run the unit tests
    user@vm:~$ cd repy_v2/
    user@vm:~/repy_v2$ mkdir test
    user@vm:~/repy_v2$ python preparetest.py -t test
    user@vm:~/repy_v2$ cd test
    user@vm:~/repy_v2/test$ python utf.py -m repyv2api


<Notes>
  This file is also used directly by trunk/dist/make_base_installers.py. Also
  let Zack know if any adaptions are made to this file so the base installers
  can continue to be created correctly.  See ticket #501 about removing or
  adapting make_base_installer.py's dependence on this file.  (Zack 7/2/09)

"""

import os
import sys
import glob
import random
import shutil
import optparse
import subprocess


# import testportfiller from root_dir\repy\tests.
sys.path.insert(0, os.path.join(os.getcwd(), "repy", "tests"))
import testportfiller
# Remove root_dir\repy\tests from the path
sys.path = sys.path[1:]

# This function copies files (in the current directory) that match the 
# expression to the target folder
# The source files are from the current directory.
# The target directory must exist.
# file_expr may contain wildcards
def copy_to_target(file_expr, target):
  files_to_copy = glob.glob(file_expr)
  for file_path in files_to_copy:
    if os.path.isfile(file_path):
      shutil.copyfile(file_path,target +"/"+os.path.basename(file_path))


def copy_tree_to_target(source, target, ignore=None):
  """
  Copies a directory to the target destination.

  If you pass a string for ignore, then subdirectories that contain the ignore
  string will not be copied over (as well as the files they contain).
  """

  full_source_path = os.path.abspath(source)
  full_target_path = os.path.abspath(target)

  for root, directories, filenames in os.walk(source):
    # Relative path is needed to build the absolute target path.

    # If we leave a leading directory separator in the relative folder
    # path, then attempts to join it will cause the relative folder path
    # to be treated as an absolute path.
    relative_folder_path = os.path.abspath(root)[len(full_source_path):].lstrip(os.sep)

    # If the ignore string is in the relative path, skip this directory.
    if ignore and ignore in relative_folder_path:
      continue

    # Attempts to copy over a file when the containing directories above it do not
    # exist will trigger an exception.
    full_target_subdir_path = os.path.join(full_target_path, relative_folder_path)
    if not os.path.isdir(full_target_subdir_path):
      os.makedirs(full_target_subdir_path)

    for name in filenames:
      relative_path = os.path.join(relative_folder_path, name)
      shutil.copyfile(
        os.path.join(full_source_path, relative_path),
        os.path.join(full_target_path, relative_path))


# Run the .mix files in current directory through the preprocessor 
# script_path specifies the name of the preprocessor script
# The preprocessor script must be in the working directory
def process_mix(script_path, verbose):
  mix_files = glob.glob("*.mix")
  error_list = []

  for file_path in mix_files:
    # Generate a .py file for the .mix file specified by file_path
    processed_file_path = (os.path.basename(file_path)).replace(".mix",".py")
    (theout, theerr) =  exec_command(sys.executable + " " + script_path + " " + file_path + " " + processed_file_path)

    # If there was any problem processing the files, then notify the user.
    if theerr:
      print "Unable to process the file: " + file_path
      error_list.append((file_path, theerr))
      
  # If the verbose option is on then print the error.  
  if verbose and len(error_list) > 0:
    print "\n" + '#'*50 + "\nPrinting all the exceptions (verbose option)\n" + '#'*50
    for file_name, error in error_list:
      print "\n" + file_name + ":"
      print error
      print '-'*80


def exec_command(command):
  # Windows does not like close_fds and we shouldn't need it so...
  process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # get the output and close
  theout = process.stdout.read()
  process.stdout.close()

  # get the errput and close
  theerr = process.stderr.read()
  process.stderr.close()

  # FreeBSD prints on stdout, when it gets a signal...
  # I want to look at the last line. It ends in \n, so I use index -2
  if len(theout.split('\n')) > 1 and theout.split('\n')[-2].strip() == 'Terminated':
    # remove the last line
    theout = '\n'.join(theout.split('\n')[:-2])
    
    # However we threw away an extra '\n'. If anything remains, let's replace it
    if theout != '':
      theout = theout + '\n'

  # OS's besides FreeBSD uses stderr
  if theerr.strip() == 'Terminated':
    theerr = ''

  # Windows isn't fond of this either...
  # clean up after the child
  #os.waitpid(p.pid,0)

  return (theout, theerr)



# Prints the given error message and the help string, then exits
def help_exit(errMsg, parser):
  print errMsg
  parser.print_help()
  sys.exit(1)

def main():

  # Parse the options provided. 
  helpstring = "python preparetest.py [-t] [-v] [-c] [-r] <target>"
  parser = optparse.OptionParser(usage=helpstring)

  parser.add_option("-t", "--testfiles", action="store_true",
                    dest="include_tests", default=False,
                    help="Include files required to run the unit tests ")
  parser.add_option("-v", "--verbose", action="store_true",
                    dest="verbose", default=False,
                    help="Show more output on failure to process a .mix file")
  parser.add_option("-c", "--checkapi", action="store_true", 
                    dest="copy_checkapi", default=False,
                    help="Include checkAPI files")
  parser.add_option("-r", "--randomports", action="store_true", 
                    dest="randomports", default=False,
                    help="Replace the default ports with random ports between \
                           52000 and 53000. ")

  (options, args) = parser.parse_args()

  # Extract the target directory.
  if len(args) == 0:
    help_exit("Please pass the target directory as a parameter.", parser)
  else:
    target_dir = args[0]

  # Make sure they gave us a valid directory
  if not( os.path.isdir(target_dir) ):
    help_exit("Supplied target is not a directory", parser)

  # Set variables according to the provided options.
  repytest = options.include_tests
  RANDOMPORTS = options.randomports
  verbose = options.verbose
  copy_checkapi = options.copy_checkapi


  # Store current directory
  current_dir = os.getcwd()

  # Set working directory to the target
  os.chdir(target_dir)	
  files_to_remove = glob.glob("*")

  # Empty the destination
  for entry in files_to_remove: 
    if os.path.isdir(entry):
      shutil.rmtree(entry)		
    else:
      os.remove(entry)

  # Return to previous working directory
  os.chdir(current_dir) 

  # Create the two required directories
  repy_dir_dict = {'repyv1' : os.path.join(target_dir, "repyV1"),
                   'repyv2' : os.path.join(target_dir, "repyV2")
                   }

  for repy_dir in repy_dir_dict.values():
    if not os.path.exists(repy_dir):
      os.makedirs(repy_dir)


  # Copy the necessary files to the test folder
  copy_to_target("repy/*", target_dir)
  copy_to_target("repy/*", os.path.join(target_dir,"repyV2"))
  copy_to_target("repy/repyV1/*", os.path.join(target_dir,"repyV1"))
  copy_to_target("nodemanager/*", target_dir)
  copy_to_target("portability/*", target_dir)
  copy_to_target("portability/*", os.path.join(target_dir,"repyV2"))
  copy_to_target("seattlelib/*", target_dir)
  copy_to_target("seattlelib/dylink.repy", os.path.join(target_dir, "repyV2"))
  copy_to_target("seattlelib/textops.py", os.path.join(target_dir, "repyV2"))
  copy_to_target("nodemanager/servicelogger.py", os.path.join(target_dir, "repyV2"))
  copy_to_target("seash/*", target_dir)
  copy_tree_to_target("seash/pyreadline/", os.path.join(target_dir, 'pyreadline/'), ignore=".svn")
  copy_tree_to_target("seash/modules/", os.path.join(target_dir, 'modules/'), ignore=".svn")
  copy_to_target("seattlegeni/xmlrpc_clients/*", target_dir)
  copy_to_target("affix/*", target_dir)
  #copy_to_target("shims/proxy/*", target_dir)
  copy_to_target("softwareupdater/*", target_dir)
  copy_to_target("autograder/nm_remote_api.mix", target_dir)
  copy_to_target("keydaemon/*", target_dir)
  copy_to_target("dist/update_crontab_entry.py", target_dir)
  # The license must be included in anything we distribute.
  copy_to_target("LICENSE.TXT", target_dir)

  # CheckAPI source
  if copy_checkapi:
    copy_to_target("checkapi/*", target_dir)
  
  if repytest:
    # Only copy the tests if they were requested.
    copy_to_target("repy/tests/restrictions.*", target_dir)
    copy_to_target("utf/*.py", target_dir)
    copy_to_target("utf/tests/*.py", target_dir)
    copy_to_target("repy/testsV2/*", target_dir)
    copy_to_target("nodemanager/tests/*", target_dir)
    copy_to_target("portability/tests/*", target_dir)
    copy_to_target("seash/tests/*", target_dir)
    copy_tree_to_target("seash/tests/modules/", os.path.join(target_dir, 'modules/'), ignore=".svn")
    copy_to_target("seattlelib/tests/*", target_dir)
    #copy_to_target("keydaemon/tests/*", target_dir)
    copy_to_target("shims/tests/*", target_dir)

    # The web server is used in the software updater tests
    #copy_to_target("assignments/webserver/*", target_dir)
    #copy_to_target("softwareupdater/test/*", target_dir)

  # Set working directory to the target
  os.chdir(target_dir)

  # Set up dynamic port information
  if RANDOMPORTS:
    print "\n[ Randomports option was chosen ]\n"+'-'*50
    ports_as_ints = random.sample(range(52000, 53000), 5)
    ports_as_strings = []
    for port in ports_as_ints:
      ports_as_strings.append(str(port))
    
    print "Randomly chosen ports: ", ports_as_strings
    testportfiller.replace_ports(ports_as_strings, ports_as_strings)

    # Replace the string <nodemanager_port> with a random port
    random_nodemanager_port = random.randint(53000, 54000)
    print "Chosen random nodemanager port: " + str(random_nodemanager_port)
    print '-'*50 + "\n"
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*nm*")
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*securitylayers*")

  else:
    # Otherwise use the default ports...
    testportfiller.replace_ports(['12345','12346','12347', '12348', '12349'], ['12345','12346','12347', '12348', '12349'])

    # Use default port 1224 for the nodemanager port if --random flag is not provided.
    replace_string("<nodemanager_port>", '1224', "*nm*")
    replace_string("<nodemanager_port>", '1224', "*securitylayers*")


  os.chdir("repyV1")
  process_mix("repypp.py", verbose)


  # Change back to root project directory
  os.chdir(current_dir) 





def replace_string(old_string, new_string, file_name_pattern="*"):
  """
  <Purpose>
    Go through all the files in the current folder and replace
    every match of the old string in the file with the new
    string.

  <Arguments>
    old_string - The string we want to replace.
 
    new_string - The new string we want to replace the old string
      with.

    file_name_pattern - The pattern of the file name if you want
      to reduce the number of files we look at. By default the 
      function looks at all files.

  <Exceptions>
    None.

  <Side Effects>
    Many files may get modified.

  <Return>
    None
  """

  for testfile in glob.glob(file_name_pattern):
    # Read in the initial file.
    inFile = file(testfile, 'r')
    filestring = inFile.read()
    inFile.close()

    # Replace any form of the matched old string with
    # the new string.
    filestring = filestring.replace(old_string, new_string)

    # Write the file back.
    outFile = file(testfile, 'w')
    outFile.write(filestring)
    outFile.close()





if __name__ == '__main__':
  main()
