"""
Ensure that modules that have conflicting commands do not get imported.
It should also display a readable error message indicating where the conflicting
command was found.
"""

import seash_dictionary
import seash_modules
#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)

#pragma out Module cannot be imported due to the following conflicting command:
#pragma out show (default)

import seash
seash.command_loop([
  'enable conflict'
])