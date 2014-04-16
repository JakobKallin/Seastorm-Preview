#!/usr/bin/env python
"""
   Author: Justin Samuel

   Start Date: 3 July 2009
   
   This will script will run the unit tests in each of the files in the unit/
   directory.

   To create a new test case (one or more tests in a single file), create a new
   module in the unit/ directory. The module can have any name, but should try
   to be descriptive of what is in there. Then make a single class in that
   module named TheTestCase (best to just copy an existing module).

   The tests themselves (the methods in TheTestCase that should be run) should
   start with 'test'.

   Note: currently this script needs to be called from the same directory
   as it resides in. Use the 'run_tests.sh' script to make sure that happens
   no matter what your current working directory is.
"""

import os
import sys
import unittest
from glob import glob

sys.path.insert(0, "unit")

# Add to the path the directory that the lockserver module is in ('../').
# This assumes that the script will be run from the tests/ directory which
# is one directory below where the lockserver_daemon.py file is.
sys.path.append('..')

# Names of modules in the unit/ directory (excluding the '.py') whose test case
# won't be run.
ignoretests = []

# Don't set this. It is populated by the loop below.
tests = []

for file in glob("unit/*.py"):
    modulename = os.path.basename(file).split(".")[0]
    if modulename in ignoretests:
      continue
    module = __import__(modulename)
    tests.append(unittest.makeSuite(module.TheTestCase))


allTests = unittest.TestSuite(tests)
runner = unittest.TextTestRunner(verbosity=2)

testresult = runner.run(allTests)

if not testresult.wasSuccessful():
  sys.exit(1)

