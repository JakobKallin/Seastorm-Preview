"""
Joins two nodes owned by guest0 and splits them again using resources.offcut
to test if the two commands work properly on the basic scale.
"""
#pragma out
import seash
import sys


command_list = [
  'loadkeys guest3', 
  'as guest3', 
  'browse', 
  'on browsegood', 
  'update', 
  'join', 
  'on %3', 
  'split resources.offcut'
  ]

seash.command_loop(command_list)
