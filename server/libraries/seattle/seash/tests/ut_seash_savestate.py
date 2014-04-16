"""
Sets up a basic working state, saves it, and reloads it again to make sure
that seash restores the state of being on a target to execute the command
'show files'.
"""
#pragma out

import seash

command_list = [
  'loadkeys guest0',
  'as guest0',
  'browse',
  'on %1',
  'savestate testing_state'
  ]

seash.command_loop(command_list)


# If loadstate was executed correctly, guest0 should have been restored to being
# on target %1, and the command 'show files' should not throw an error
command_list = [
  'loadkeys guest0',
  'as guest0',
  'loadstate testing_state',
  'show files'
  ]

seash.command_loop(command_list)
