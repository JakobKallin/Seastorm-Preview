"""
Test commands that manipulate the modules within seash

"""
import sys
import seash
import seash_dictionary
import seash_modules

#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


oldstdout = sys.stdout
sys.stdout = open('test_results.txt', 'w')


seash.command_loop([
  'show modules',
  'enable geoip',
  'show modules',
  'modulehelp geoip',
  'disable geoip',
])

sys.stdout = oldstdout
expected_lines = open('modulemanipulation_test_results.txt', 'r').readlines()
actual_lines = open('test_results.txt', 'r').readlines()

for lineno in xrange(len(actual_lines)):
  if expected_lines[lineno] != actual_lines[lineno]:
    print "Line", lineno, "of test results are not consistent with expected results: modulemanipulation_test_results.txt"