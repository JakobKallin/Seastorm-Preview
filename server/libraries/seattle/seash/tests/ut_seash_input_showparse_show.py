"""
Make sure that preprocessed command line input is printed to the screen
"""

import seash
import seash_dictionary
import seash_modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


#pragma out Enabled modules:

#pragma out loadkeys guest0
#pragma out as guest0

seash.command_loop([
  'enable variables',
  'set username guest0',
  'loadkeys $username',
  'as $username$',
  'disable variables'])