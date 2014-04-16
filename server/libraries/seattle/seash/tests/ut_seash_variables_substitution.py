"""
Makes sure the Variables module for seash works as intended.
In particular, we check that the $varname and $varname$ methods of referencing
variables are functional.
"""

import seash

import seash_dictionary
import seash_modules

#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)

seash.command_loop([
  'enable variables',
  'set helpcmd help',
  '$helpcmd',
  '$helpcmd show',
  '$helpcmd$',
  '$helpcmd$ show',
  'disable variables',
])