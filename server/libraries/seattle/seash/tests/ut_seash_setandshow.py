"""
Runs a series of set and show commands to make sure no errors are being thrown
during command executions. Due to variations in output caused by the user's
IP address, output results are not being tested too extensively.
"""
import seash
import sys


orig_stdout = sys.stdout

# To temporarily prevent printing to console, test_results.txt is used as a text
# dump as stdout is redirected to it
sys.stdout = open("test_results.txt", "w")

command_list = [
  'loadkeys guest0', 
  'loadkeys guest1', 
  'loadkeys guest2', 
  'as guest1', 
  'browse', 
  'on browsegood', 
  'show info', 
  'update', 
  'show info', 
  'show users', 
  'set users guest0 guest1 guest2', 
  'show users', 
  'show ownerinfo', 
  'set ownerinfo example text testing', 
  'show ownerinfo', 
  'set advertise off', 
  'show advertise', 
  'set advertise on', 
  'show ip', 
  'show ip to test_ip_file.txt', 
  'show hostname',
  'show targets', 
  'show resources', 
  'show offcut', 
  'savestate testing_state', 
  'on %1', 
  'show owner', 
  'set owner guest2', 
  'show owner'
  ]

seash.command_loop(command_list)

sys.stdout.close()



# Overwrites test_results.txt for a clean file for actual testing purposes.
sys.stdout = open("test_results.txt", "w")

command_list = [
  'loadkeys guest1', 
  'as guest1', 
  'loadstate testing_state', 
  'show timeout', 
  'set timeout 123', 
  'show timeout', 
  'show uploadrate', 
  'set uploadrate 2048', 
  'show uploadrate'
  ]

seash.command_loop(command_list)

sys.stdout.close()



# Simple test to see that seash records the values for timeout and uploadrate
# when changed
sys.stdout = orig_stdout

test_results = open("test_results.txt", "r")
wanted_results = open("setandshow_test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i] == actual[i]:
    print "Line " + str(i) + " of test_results.txt are not consistent with expected results in setandshow_test_results.txt"

test_results.close()
wanted_results.close()
