"""
Sets up the local node manager processes for certain tests
"""

import subprocess
import sys
import harshexit
import os
import glob
import shutil

initproc = subprocess.Popen([sys.executable, "nminit_test.py"])
initproc.wait()

nmproc = subprocess.Popen([sys.executable, "nmmain.py", "--test-mode"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# without closing stdin, stdout, stderr, nmmain.py won't execute on XP
nmproc.stdin.close()
nmproc.stdout.close()
nmproc.stderr.close()


try:
  # We'll want to kill this once we are told to do so... (sys.stdin.close() is
  # the signal)
  sys.stdin.read()
except KeyboardInterrupt:
  # the user interrupted us, let's clean up!
  print
  print 'Cleaning up the subprocess'

# We need the PID.   Since the node manager daemonizes, this isn't the pid of
# nmproc.   We can get the PID from the log
nodemanagerlogfo = open('v2'+os.sep+'nodemanager.old')

firstline = nodemanagerlogfo.readline()

# an entry looks like this:
# 1292537407.82:PID-27493:[INFO]: Running nodemanager in test mode
# let's get the PID out as a number...
pidportion = firstline.split(':')[1]
assert(pidportion.startswith('PID-'))
nmpid = int(pidportion[4:])

# let's terminate the node manager...
harshexit.portablekill(nmpid)

# remove the directories and files created by nminit_test.py
# first, let's clean up any existing directory data...
for vesseldirectoryname in glob.glob('v[0-9]*'):
  if os.path.isdir(vesseldirectoryname):
    print 'Removing:',vesseldirectoryname
    shutil.rmtree(vesseldirectoryname)

# remove resource files created by nminit_test.py
for resourcefilename in glob.glob('resource.v*[0-9]'):
  if os.path.isfile(resourcefilename):
    os.remove(resourcefilename)

# remove example repy files created from downloading from node
for repyfiles in glob.glob('example.1.1.repy.*'):
  if os.path.isfile(repyfiles):
    os.remove(repyfiles)

# remove other files created by nminit_test.py
os.remove("resources.offcut")
os.remove("vesseldict")
