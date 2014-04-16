"""
Makes sure the Variables module for seash works as intended.
In particular, we check that trailing delimiters are not recognized as a
variable.
"""
import seash
import seash_dictionary
import seash_exceptions
import seash_modules

#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


# This error should come up since %all contains nothing as we don't browse for
# anything prior to this.  This is not a problem though as we are just testing
# the trailing $ in a command.
try:
  seash.command_loop([
    'enable variables',
    'add %all to $',
  ])
except seash_exceptions.UserError, e:
  if not "No targets to add (the target is already in '$'" in str(e):
    raise

seash.command_loop(['disable variables'])