"""
<Program>
  exceptions.py

<Started>
  6 July 2009

<Author>
  Justin Samuel
  
<Purpose>
  All exceptions used outside of a single module in seattlegeni are defined
  in this file. All seattlegeni modules should import all exceptions in this
  file. That is, the following code should be at the top of all seattlegeni
  modules:
  
  from seattlegeni.common.exceptions import *
  
  This ensures that we don't end up ever having an exception named in a
  try/catch block that isn't actually defined in that modules namespace.
  
  Note: We define __all__ at the bottom of this script to make sure that we
  only export the exceptions we've defined here, not anything else that may be
  imported or used in this module. Only names that end in "Error" are exported.
  
  In general, no code in seattlegeni should knowingly let built-in
  python exceptions escape from the place where the exception occurs.
  Instead, it should be caught and, if it can't be dealt with, re-raised as
  one of the exceptions in this module (with the details of the original
  exception in the message). Generally this will be either raising the
  exception as a ProgrammerError or an InternalError. That is, if it's
  something we can't recover from, it's usually either bad code or something
  broken/a service down.
"""

# TODO: allow construction of the exceptions and passing them another exception as
# an argument, where the details of that other exception will also be printed
# when the new exception's details are.

class SeattleGeniError(Exception):
  """
  <Purpose>
    All other custom exceptions of seattlegeni inherit from this.
  """



class InvalidRequestError(SeattleGeniError):
  """
  Indicates that a requested action was invalid. This is an intentionally
  generic error. This error should be raised with a message that clearly
  explains what was invalid.
  """



class ProgrammerError(SeattleGeniError):
  """
  Indicates that a programmer is using something incorrectly. Rather than
  extend this class for many different cases, this error should be raised
  with a message that clearly explains what the programmer did wrong
  (for example, they passed an argument of the wrong type into a function).
  
  Do not catch this exception! You may prevent proper notification about a
  broken part of seattlegeni. This exception will never be documented that
  it can be raised. You should assume it's always possible that it be
  raised. If you really know what you're doing, you can break this rule and
  catch a ProgrammerError.
  """
  

  
class InternalError(SeattleGeniError):
  """
  Indicates that some part of the seattlegeni system failed. E.g., a
  communication problem with the lockserver, backend, or database. Can also
  indicate the database is in a bad state. The text of the raised exception
  should clearly describe the problems and all related details.
  
  Do not catch this exception! You may prevent proper notification about a
  broken part of seattlegeni. This exception will never be documented that
  it can be raised. You should assume it's always possible that it be
  raised. If you really know what you're doing, you can break this rule and
  catch an InternalError.
  """



class NodemanagerCommunicationError(SeattleGeniError):
  """
  Indicates a failure in communication with a nodemanager.
  """



class DoesNotExistError(SeattleGeniError):
  """
  Indicates that some requested data/record does not exist.
  """



class ValidationError(SeattleGeniError):
  """
  Indicates that some data checked for validity is invalid. This is not the
  same as a django.forms.ValidationError.
  """



class UsernameAlreadyExistsError(SeattleGeniError):
  """
  Indicates that registration of a username was attempted but that there
  is already a user with this username.
  """
  
  
  
class UnableToAcquireResourcesError(SeattleGeniError):
  """
  Indicates that SeattleGeni was unable to satisfy a request for resource
  acquisition.
  """

  
  
class InsufficientUserResourcesError(SeattleGeniError):
  """
  Indicates that a user requested more resources than they are allowed to have.
  """



class TimeUpdateError(SeattleGeniError):
  """
  Indicates that a call to the time_updatetime() repy function failed. This is
  to avoid this situation being treated as an InternalError in case it's
  considered to be non-fatal at some point in the future.
  """



# Many modules are using the line 'from seattlegeni.common.exceptions import *'
# to import the exceptions. We define __all__ so that we only export names from
# this module that end in the word "Error". 
__all__ = []
for name in dir():
  if name.endswith("Error"):
    __all__.append(name)

