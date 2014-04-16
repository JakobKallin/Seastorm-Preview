"""
<Author>
  richard@jordan.ham-radio-op.net

<Start Date>
  April 05, 2009

<Description>
  Distutils script.  Distutils is the classic python way to
  automate.  It supposingly takes care of portability for you.
  Also, you can register with Cheese Shop (PyPI) for easy distribution.

  Usually, it manages Python modules.  We're more into Python
  scripts, so we customize it all a bit.

  Also, we add some extra handy commands.

  References:
    http://da44en.wordpress.com/2002/11/22/using-distutils/
    http://docs.python.org/distutils/
    http://blog.ianbicking.org/pythons-makefile.html
    http://wiki.python.org/moin/Distutils/Tutorial

<Usage>
  python setup.py ...
 
  Do `python setup.py --help-commands` for available commands.
"""
# standard imports
from distutils.cmd import Command
from distutils.errors import *
from distutils.core import setup

# commands to customize
import distutils.command.build_scripts
import distutils.command.clean


# other python libs
import preparetest
import os
import shutil
import glob
import tempfile


#######################
# New Commands
#######################

class test(Command):
    """
    <Purpose>
      This command calls a script that erases all the files in a target folder, 
      then copies the necessary test files to the folder. Afterwards, the .mix files 
      in the target folder are run through the preprocessor. 
 
      If the folder doesn't exist, this command *will* create it for you.
    """
    description = "run the seattle preparetest.py script"
    user_options = [('include-repy-tests', 't', 'copy in the repy test files')]
    boolean_options = ['t']

    def initialize_options(self):
      """Setup defaults"""
      self.directory = "tests"
      self.include_repy_tests = False	
	
    def finalize_options(self):
      """ What do we have?"""
      pass

    def run(self):
      """Do a little setup, then pass off to old python script"""

      # remove dir if exists and recreate it. other wise create it
      refresh_dir(self.directory)

      # pass off to preparetest.py
      cmd = "python preparetest.py " + str(self.directory)
      if self.include_repy_tests:
        cmd += " -t"
      preparetest.exec_command(cmd)

class demokit(Command):
    """
    <Purpose>
      This command generates a folder of Repy and some
      other files.  This generated demokit folder is a distribution of Repy.

      Creates a directory called "demokit".  If "demokit" exists,
      overwrites it.

      Uses the build_scripts command to generate Repy and Seash scripts.
    """
    description = "build the demokit"
    user_options = []

    def initialize_options(self):
      """Setup defaults"""
      self.directory = "demokit"

    def finalize_options(self):
      """See what we have"""
      pass

    def run(self):
      """Do it"""
      #store root directory and get target directory
      target_dir = self.directory

      # remove dir if exists and recreate it. other wise create it
      refresh_dir(target_dir)

      # Build Repy
      builder =build_scripts(self.distribution)
      builder.finalize_options()
      builder.run()

      # Add the files
      preparetest.copy_to_target("build/scripts-2.5/repy.py", target_dir)
      preparetest.copy_to_target("build/scripts-2.5/seash.py", target_dir)
      preparetest.copy_to_target("seattlelib/repypp.py")
      preparetest.copy_to_target("repy/apps/allpairsping/allpairsping.repy", target_dir)
      preparetest.copy_to_target("repy/apps/old_demokit/*", target_dir)
      preparetest.copy_to_target("LICENSE.TXT", target_dir)


#######################
# Custom Standard Commands
#######################

class clean(distutils.command.clean.clean):
    """
    <Purpose>
      This command removes the junk of other commands.  It also deletes .pyc
      files.  And does whatever the usual clean would do
    """

    description = "clean up temporary files from the 'build', 'test', 'demokit' commands"

    def initialize_options(self):
      """Setup"""

      # super
      distutils.command.clean.clean.initialize_options(self)

      # these are the junk dirs from other commands
      self._junk = ['demokit', 'tests']

    def run(self):
      """Delete it all"""
      # super
      distutils.command.clean.clean.run(self)

      # Remove .pyc files
      pycs = [ ]
      for dirpath, dirnames, filenames in os.walk('.'):
        for fname in filenames:
          if fname.endswith('.pyc'):
            os.remove(os.path.join(dirpath, fname))
         
      # Remove junk directories
      for junker in self._junk:
        if (os.path.exists(junker)):
          if os.path.isdir(junker):
            shutil.rmtree(junker)
          else:
            os.remove(junker)


class build_scripts(distutils.command.build_scripts.build_scripts):
    """
    <Purpose>
      This command generates portable versions of our scripts.  But first,
      we squeeze our scripts into single files.
    """
    def initialize_options(self):
      """Setup"""

      # super
      distutils.command.build_scripts.build_scripts.initialize_options(self)

      # these are files needed (included/imported) to build each script
      repy_core = ['repy/*.py', 'nodemanager/servicelogger.mix', 'seattlelib/*.repy', 'nodemanager/persist.py']
      nm_core = ['nodemanager/*.mix', 'nodemanager/*.py']
      self._dependencies = { 
		'repy.py': repy_core, 
		'seash.py': ['seash/seash.mix', 'portability/repyportability.py'] + repy_core + nm_core, 
		'rhizoma.py': ['seattlelib/rhizoma.mix', 'portability/repyportability.py', 'autograder/nm_remote_api.mix'] + repy_core + nm_core}

    def run(self):
      """Process, squeeze, call super, and then clean up"""

      # this will dump a processed-squeezed version each script
      # into the current directory
      for script in self.scripts:
        # create a temporary file 
        tmpdirname = tempfile.mkdtemp()
        # copy and process repy in the tmp directory
        process_it(script, self._dependencies[script], tmpdirname)
        squeeze_it(script, tmpdirname)
        # clean up
        shutil.rmtree(tmpdirname)

      # now do the usual with the newly created scripts
      distutils.command.build_scripts.build_scripts.run(self)

      # then remove the tmp squeezed ones
      for script in self.scripts:
        os.remove(script)

######################
# Helpers
####################

def refresh_dir(directory):
  """Creates the directory, or deletes and recreates."""
  # remove dir if exists
  if (os.path.exists(directory)):  
    if os.path.isdir(directory):
      shutil.rmtree(directory)
    else:    
      os.remove(directory)
  # recreate it
  os.mkdir(directory)    


def squeeze_it(script, tmpdirname):
  """
  <Purpose>
    Turn a bunch of python files into one compressed file
   
  <Args>
    script - the main module to start at
    tmpdirname - the directory with all the dependent files 

  <Pre>
    Process all files using process_it() into the tmp dir.
    The files in the tmp should be the minimal set of files.

  <Side Effect>
    Dumps the compressed script into the current directory
  """
  fileglob = tmpdirname + "/*.py"
  scriptnameonly = os.path.splitext(os.path.basename(script))[0]
  cmd = "python squeeze.py -1 -o " + scriptnameonly + " -b " + scriptnameonly + " " + fileglob
  preparetest.exec_command(cmd)


def process_it(script, dependencies, tmpdirname):
   """
   <Purpose>
     Copy into the directory and process all the files needed for the script.
     Remove unneeded files after processing.

   <Args>
     script - the main module to build
     dependencies - the files the main script includes or imports
     tmpdirname - the temporary directory
   <Side Effects>
     Leaves the minimal set of files neccessary to run the script in the tmp dir
   """

   target_dir = tmpdirname
   current_dir = os.getcwd()

   # copy them all in
   for filepath in dependencies:
     preparetest.copy_to_target(filepath, target_dir)

   # add some utils
   preparetest.copy_to_target("seattlelib/repypp.py", target_dir)

   #set working directory to the test folder
   os.chdir(target_dir)

   #call the process_mix function to process all mix files in the target directory
   preparetest.process_mix("repypp.py")

   # rm build files
   files_to_remove = glob.glob("*.mix") + glob.glob("*.repy")
   for fn in files_to_remove: 
     os.remove(fn)
   os.remove("repypp.py") # get rid of the repypp.py file

   #go back to root project directory
   os.chdir(current_dir) 

#################
# Main
#################
"""
<Purpose>
  Main interface to Distutils.

<Usage>
  cmdclass
    Add new commands to the cmdclass dictionary.

  scripts
    Add other scripts here and modify build_scripts
    to correctly build them.
 
<Else>
  All other details are metadata.  Distutils uses
  then to register your project with Cheese Shop
  as well as generate user help messages.
"""

commandClasses = dict(
      test = test,
      demokit = demokit,
      clean = clean,
      build_scripts = build_scripts)

setup(name = "Seattle",
      version = "0.1e",
      author = 'Justin Cappos', 
      author_email="seattle-devel@cs.washington.edu",	
      maintainer = 'Ivan Beschastnikh',
      maintainer_email="seattle-devel@cs.washington.edu",	
      url = "http://seattle.cs.washington.edu",
      description = "a platform for networking and distributed systems research",
      long_description = """
Seattle is a platform for networking and distributed systems research. It's free, community-driven, and offers a large deployment of computers spread across the world. 
Seattle works by operating on resources donated by users and institutions. It's currently targeted for use by educators teaching networking and distributed systems 
classes. The global distribution of the Seattle network provides the ability to use it in application contexts that include cloud computing, peer-to-peer networking, 
ubiquitous/mobile computing, distributed systems. 
""",
      keywords = "seattle repy",
      license = "GENI Public License",

      scripts = ['repy.py', 'seash.py', 'rhizoma.py'],
      cmdclass = commandClasses)

