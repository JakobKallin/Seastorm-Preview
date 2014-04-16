"""
Ensure that all modules do not conflict with each other

"""
#pragma out
import os
import seash

import seash_dictionary
import seash_modules
#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


commands = [
  # Enable all the modules
  'enable geoip',
  'enable factoids',
  'enable variables',
  # Disable all the modules
  'disable geoip',
  'disable factoids',
  'disable variables',
  ]

seash.command_loop(commands)