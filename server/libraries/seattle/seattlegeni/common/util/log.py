"""
<Program>
  log.py

<Started>
  6 July 2009

<Author>
  Justin Samuel

<Purpose>
  This module provides logging functionality to be used within seattlegeni.
  All seattlegeni code should log through this module rather than using
  print() or directly using the repy logging module. This ensures that only
  one module (this one) determines where log messages actually go for all
  of seattlegeni. (This module may in turn use the repy logging module, but
  client code should be unaware of that.)
  
  Logging output done by this module will try to include a request_id with
  each log message so that it is possible to differentiate multiple requests
  or threads running at the same time.
  
  Currently, our custom django middleware at website/middleware/logrequest.py
  calls log_start_request() when a new request comes in.
  
  Using this module from outside of a django website means that client code
  should first call log_start_request() or set_request_id() if it wants
  log messages from a thread to be logged with an identifier.
"""

import random
import sys
import threading
from datetime import datetime




# We use a thread-local data store for tracking the request identifier
# so that we can log the associated request id even when the request
# object isn't among a function's arguments.
request_context = threading.local()





LOG_LEVEL_DEBUG = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_ERROR = 3
LOG_LEVEL_CRITICAL = 4
LOG_LEVEL_NONE = 5

# Default log level of DEBUG.
loglevel = LOG_LEVEL_DEBUG





def set_log_level(level):
  global loglevel
  loglevel = level





def debug(message):
  if loglevel <= LOG_LEVEL_DEBUG:
    print >> sys.stderr, _get_time() + " DEBUG " + _get_request_id() + " " + str(message)
    sys.stderr.flush()





def info(message):
  if loglevel <= LOG_LEVEL_INFO:
    print >> sys.stderr, _get_time() + " INFO " + _get_request_id() + " " + str(message)
    sys.stderr.flush()





def error(message):
  if loglevel <= LOG_LEVEL_ERROR:
    print >> sys.stderr, _get_time() + " ERROR " + _get_request_id() + " " + str(message)
    sys.stderr.flush()





def critical(message):
  if loglevel <= LOG_LEVEL_CRITICAL:
    print >> sys.stderr, _get_time() + " CRITICAL " + _get_request_id() + " " + str(message)
    sys.stderr.flush()





def _get_request_id():
  if not hasattr(request_context, 'request_id'):
    set_request_id()
  return request_context.request_id





def _get_time():
  return "[" + datetime.now().isoformat(' ') + "]"





def log_start_request(request):
  """
  Create a unique request id and store it in request_context if it isn't
  already set there. This way it will be available to future log calls.
  """
  request_id = _generate_request_id_from_request(request)
  set_request_id(request_id)

  messagelist = []

  messagelist.append("Request started.")
  
  # See http://docs.djangoproject.com/en/dev/ref/request-response/ for a list
  # of attributes of the HttpRequest object that we could potentially log.
  messagelist.append(request.method)
  messagelist.append(request.path)
  
  # Log the request variables.
  # We ignore the fact that there could be query string variables in a POST request.
  if request.method == "GET":
    messagelist.append(str(request.GET))
  else:
    clean_post_querydict = request.POST.copy()
    for key in request.POST:
      # TODO: need to prevent logging password/apikey in xmlrpc requests
      if "password" in key:
        clean_post_querydict[key] = "[REMOVED]"
    messagelist.append(str(clean_post_querydict))
  
  if request.user.is_authenticated():
    messagelist.append("logged_in_user:" + str(request.user.username))
  else:
    messagelist.append("logged_in_user:-")
  
  info(' '.join(messagelist))





def set_request_id(request_id=None):
  """
  Sets the request id. This will be used in all future log messages performed
  by the current thread.
  """
  if request_id is None:
    request_id = _generate_request_id()
    
  request_context.request_id = str(request_id)





def _generate_request_id():
  RANDMIN = 100000000
  RANDMAX = 999999999
  return str(random.randint(RANDMIN, RANDMAX))





def _generate_request_id_from_request(request):
  """
  Create a unique tag for the request, to make it easier to follow its log
  entries.
  
  Based on the idea from:
  http://www.fairviewcomputing.com/blog/2008/03/05/django-request-logging/
  """
  # If Apache's mod_unique_id is in use, use that. Otherwise, create one.
  if request.META.has_key('UNIQUE_ID'):
    return str(request.META['UNIQUE_ID'])
  else:
    return _generate_request_id()

