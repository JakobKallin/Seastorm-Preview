"""
Executes a few help commands and make sures seash prints out the correct output.
Make sure to update the txt file of the expected output if help's contents have
modified
"""
import seash
import sys


orig_stdout = sys.stdout
sys.stdout = open("test_results.txt", "w")
command_list = [
  'help', 
  'help extended', 
  'help show', 
  'help show info', 
  'help show ip to file'
  ]

seash.command_loop(command_list)

sys.stdout.close()


# Compares the test results with the expected text that should have been printed
# out when executing the series of help commands
sys.stdout = orig_stdout

test_results = open("test_results.txt", "r")
wanted_results = open("help_test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i] == actual[i]:
    print "Line " + str(i) + " of test results are not consistent with expected results: help_test_results.txt"

test_results.close()
wanted_results.close()

