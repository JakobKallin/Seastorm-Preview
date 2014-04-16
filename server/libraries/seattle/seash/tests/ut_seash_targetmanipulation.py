"""
Performs a few basic commands in creating groups and moving targets around.
No errors or exceptions should be thrown.
"""

import seash
import sys

orig_stdout = sys.stdout

# To temporarily prevent printing to console, test_results.txt is used as a text
# dump as stdout is redirected to it
sys.stdout = open("test_results.txt", "w")

command_list = [
  'loadkeys guest0', 
  'as guest0', 
  'browse', 
  'on %1', 
  'savestate testing_state'
  ] 

seash.command_loop(command_list)

sys.stdout.close()



# No output or errors should be thrown in the following series of commands
sys.stdout = orig_stdout

command_list = [
  'loadkeys guest0', 
  'as guest0', 
  'loadstate testing_state', 
  'add to test_group', 
  'remove %1 from test_group', 
  'add %1 to test_group_2',
  'on %2', 
  'move %2 to test_group'
  ]

seash.command_loop(command_list)
