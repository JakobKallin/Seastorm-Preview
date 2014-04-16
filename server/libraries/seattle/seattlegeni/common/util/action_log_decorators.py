"""
<Program>
  action_log_decoratorss.py

<Started>
  Oct 16, 2009

<Author>
  Justin Samuel

<Purpose>
  These define the decorators used to log "actions" to the database.
  
  These are mostly intended to be actions involving vessels such as
  acquiring, releasing, renewing, and expiring vessels (see the models for
  ActionLogEvent and ActionLogVesselDetails for additional information about
  how the data is stored).
"""

import datetime

from seattlegeni.common.api import maindb

from seattlegeni.common.util import decorators

from seattlegeni.website.control import models




def _is_vessel_list(potential_vessel_list):
  """Determine if potential_vessel_list is a list of Vessel objects."""
  
  if not isinstance(potential_vessel_list, list):
    return False

  for i in potential_vessel_list:
    if not isinstance(i, models.Vessel):
      return False
    
  if len(potential_vessel_list) == 0:
    return False
  
  return True





@decorators._simple_decorator
def log_action(func):
  """
  <Purpose>
    Logs information in the database, mostly intended to be actions involving
    vessels (see the models for ActionLogEvent and ActionLogVesselDetails).
  """
  
  # The name "do_logging_func_call" is never seen anywhere but here.
  def do_logging_func_call(*args, **kwargs):
    
    # We are actually going to ignore kwargs and assume keyword arguments
    # aren't being used for the interface calls we are logging with this.
    
    date_started = datetime.datetime.now()
    
    user = None
    second_arg = None
    third_arg = None
    vessel_list = []
    
    # Check if the first arguments is a GeniUser object. We expect it to
    # always be at the moment, so this is just in case things change.
    if args and isinstance(args[0], models.GeniUser):
      user = args[0]
    
    # The interface calls we're using this decorator on may have one or two
    # additional arguments after the geniuser object. If they exist, they
    # are either vessel lists or other values we want to log.
    if len(args) > 1:
      if _is_vessel_list(args[1]):
        vessel_list = args[1]
      else:
        second_arg = str(args[1])
      
    if len(args) > 2:
      if _is_vessel_list(args[2]):
        vessel_list = args[2]
      else:
        third_arg = str(args[2])
    
    try:
      result = func(*args, **kwargs)
      # If a vessel list is returned, that's the one we want even if we took
      # one in as an argument.
      if _is_vessel_list(result):
        vessel_list = result
      was_successful = True
      message = None
      maindb.create_action_log_event(func.__name__, user, second_arg,
                                     third_arg, was_successful, message,
                                     date_started, vessel_list)
      return result
    
    except Exception, e:
      was_successful = False
      message = str(e)
      maindb.create_action_log_event(func.__name__, user, second_arg,
                                     third_arg, was_successful, message,
                                     date_started, vessel_list)
      raise
    
  return do_logging_func_call
