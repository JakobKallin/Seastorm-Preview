"""
<Author>
  Evan Meagher
  
<Started>
  March 2010

<Description>
  Builds a downloadable demokit from Seattle files and demo applications in
  trunk.
  
  Usage: usage: python build_demokit.py path/to/trunk/ output/dir/
  
  Example usage:
    python ./Seattle/trunk/dist/build_demokit.py ./Seattle/trunk/ ./demokit/
"""

import os
import sys
import shutil
import subprocess
import tempfile
import tarfile
import clean_folder

# Name to give base directory of demokit
BASE_DEMOKIT_DIR = "seattle_demokit"



def prepare_files(trunk_location, temp_demokit_dir):
  """
  <Purpose>
    Prepare the general Seattle files and deposit them into the designated
    temporary directory.

  <Arguments>
    trunk_location:
      The path to the trunk of the repository.

    temp_demokit_dir:
      The temporary directory where the general files to be included in the
      demokit will be placed.

  <Exceptions>
    IOError on bad file paths.    

  <Side Effects>
    All general files are placed into the specified temporary directory.

  <Returns>
    None.
  """

  # Run preparetest to generate and place all general Seattle files in the
  # temporary directory.

  # To run /trunk/preparetest.py, we must be in that directory (a bug in
  # preparetest.py?)
  original_dir = os.getcwd()
  os.chdir(trunk_location)
  p = subprocess.Popen(["python",
                        trunk_location + os.sep + "preparetest.py",
                        temp_demokit_dir])
  p.wait()
  os.chdir(original_dir)


  # Copy necessary Seattle files
  # shutil.copy2(trunk_location + os.sep + "experimentmanager/experimentlib.py", temp_demokit_dir)
  # shutil.copy2(trunk_location + os.sep + "seattlegeni/xmlrpc_clients/seattleclearinghouse_xmlrpc.py", temp_demokit_dir)
  # shutil.copy2(trunk_location + os.sep + "experimentmanager/repyimporter.py", temp_demokit_dir)

  # Copy Seattle license file
  # shutil.copy2(trunk_location + os.sep + "LICENSE.txt", temp_demokit_dir)

  
  # Copy all demokit-specific files
  
  # Allpairsping map application
  # os.chdir(trunk_location + os.sep + "repy/apps/appmap/")
  # shutil.copy2("pingneighbors.repy", temp_demokit_dir)
  # shutil.copy2("style.css", temp_demokit_dir)
  # shutil.copy2("jquerygmaps.js", temp_demokit_dir)
  # shutil.copy2("map_marker_icon.png", temp_demokit_dir)
  # shutil.copy2("map_marker_sel_icon.png", temp_demokit_dir)
  # shutil.copy2("appmap.py", temp_demokit_dir)
  # os.chdir(original_dir)
  
  # Preprocess pingneighbors.repy
  # os.chdir(temp_demokit_dir)
  # repypp_proc = subprocess.Popen([
  #     "python", trunk_location + os.sep + "seattlelib" + os.sep + "repypp.py",
  #     temp_demokit_dir + os.sep + "pingneighbors.repy",
  #     temp_demokit_dir + os.sep + "pingneighbors.py"])
  # repypp_proc.wait()
  # Now remove unprocessed pingneighbors.repy
  # os.remove(temp_demokit_dir + os.sep + "pingneighbors.repy")

  # Original allpairsping demo
  # os.chdir(trunk_location + os.sep + "repy/apps/allpairsping/")
  # shutil.copy2("allpairsping.repy", temp_demokit_dir)
  # os.chdir(original_dir)

  # UDP ping demos
  # os.chdir(trunk_location + os.sep + "repy/apps/udpping/")
  # shutil.copy2("udpping.repy", temp_demokit_dir)
  # shutil.copy2("udppingserver.repy", temp_demokit_dir)
  # shutil.copy2("udpforward.repy", temp_demokit_dir)
  # shutil.copy2("restrictions.allowallports", temp_demokit_dir)
  # os.chdir(original_dir)

  # infloop program from Take Home Assignment
  # os.chdir(trunk_location + os.sep + "repy/apps/infloop/")
  # shutil.copy2("infloop.repy", temp_demokit_dir)
  # os.chdir(original_dir)

  # helloworld program from Take Home Assignment
  # os.chdir(trunk_location + os.sep + "repy/apps/helloworld/")
  # shutil.copy2("helloworld.repy", temp_demokit_dir)
  # os.chdir(original_dir)


  


def package_demokit(temp_demokit_dir, temp_archive_dir):
  """
  <Purpose>
    Packages the demokit files into a tarball

  <Arguments>
    temp_demokit_dir:
      The path to the temporary demokit directory.

    temp_archive_dir:
      The path to the directory in which the demokit tarball is stored.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """

  demokit_tar = tarfile.open(temp_archive_dir + os.sep + BASE_DEMOKIT_DIR + ".tgz", "w:gz")
    
  # Put all demokit files into the tarball
  for fname in os.listdir(temp_demokit_dir):
    demokit_tar.add(temp_demokit_dir + os.sep + fname, BASE_DEMOKIT_DIR + os.sep + fname, True)

  demokit_tar.close()



  

def validate_args(arguments):
  """
  Tests arguments. Return True is valid.
  """
  # Test argument flags
  if len(arguments) != 3:
    return False

  # Test argument paths, and get their absolute paths.
  # Test trunk path.
  if not os.path.exists(arguments[1]):
    raise IOError("Trunk not found at " + arguments[1])

  # Test output directory path.
  if not os.path.exists(sys.argv[2]):
    raise IOError("Output directory does not exist.")

  
  # All arguments are valid.
  return True





def usage():
  """
  Prints usage string.
  """
  print "usage: python build_demokit.py path/to/trunk/ output/dir/"

  


  
def main():
  # Test arguments and find full pathnames.
  if not validate_args(sys.argv):
    usage()
    return

  # Reaching this point means all arguments are valid, so set the variables and
  # get full pathnames when necessary.
  trunk_location = os.path.realpath(sys.argv[1])
  output_dir = os.path.realpath(sys.argv[2])



  # Begin creating demokit
  print "Creating a demokit. This may take a moment or two."

  # Create temporary directories for the demokit files and archive
  temp_demokit_dir = tempfile.mkdtemp()
  temp_archive_dir = tempfile.mkdtemp()

  # Prepare all files to go into demokit
  prepare_files(trunk_location,temp_demokit_dir)

  # Clean the temporary directory of unnecessary files
  clean_folder.clean_folder(trunk_location + os.sep + "dist/demokit_files.fi", temp_demokit_dir)
  
  # Create archive
  package_demokit(temp_demokit_dir, temp_archive_dir)

  # Move the demokit tarball to the specified output directory
  for tarball in os.listdir(temp_archive_dir):
    shutil.copy2(temp_archive_dir + os.sep + tarball, output_dir)

  # Remove the temporary directories
  shutil.rmtree(temp_demokit_dir)
  shutil.rmtree(temp_archive_dir)

  
  print "Demokit created: " + output_dir + os.sep + BASE_DEMOKIT_DIR + ".tgz"




  
if __name__ == "__main__":
    main()
