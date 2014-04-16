"""
Make sure that preprocessed command line input is printed to the screen
"""

import sys

import seash_dictionary

#pragma out Enabled modules:
import seash

import seash_modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)

# There shouldn't be any output from here on...
# If the file has anything inside it after we're done, then it is an error.
sys.stdout = open('test_results.txt', 'w')

seash.command_loop([
  'enable variables',
  'set showparse off',
  'set username guest0',
  'loadkeys $username',
  'as $username$',
  'disable variables'])

sys.stdout.close()
sys.stdout = sys.__stdout__

test_output = open('test_results.txt', 'r').read()
if test_output:
  print test_output
  