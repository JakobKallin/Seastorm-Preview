"""
Uploads and runs a simple repy file to make sure no errors gets thrown, and
proceeds to download and remove the file from the node to test seash's file
recognition.
"""
#pragma out The specified file(s) could not be found. Please check the filename.

import seash
import sys


# Prevent printing to console by using test_results.txt as a text dump and redirecting output there
orig_stdout = sys.stdout
sys.stdout = open("test_results.txt", "w")


command_list = [
  'loadkeys guest0', 
  'as guest0', 
  'browse', 
  'on %1', 
  'loadkeys guest0', 
  'as guest0', 
  'upload example.1.1.repy sample_file', 
  'run example.1.1.repy test_argument', 
  'show log', 
  'show files', 
  'start sample_file test_argument', 
  'show log', 
  'download sample_file', 
  'savestate testing_state'
  ]

seash.command_loop(command_list)

sys.stdout.close()



# Resets stdout to allow printing to console to allow UTF to catch errors printed by seash
sys.stdout = orig_stdout

command_list = [
  'loadkeys guest0', 
  'as guest0', 
  'loadstate testing_state', 
  'delete example.1.1.repy', 
  'upload example.1.1.repy', 
  'reset', 
  'download example.1.1.repy'
]

seash.command_loop(command_list)
