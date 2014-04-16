"""
<Program>
  logexception.py

<Started>
  24 August 2009

<Author>
  Justin Samuel

<Purpose>
  We register "middleware" with django to log exceptions. By default, django
  will send an email to the admins if DEBUG is False, but it will not log
  anything.

  Documenation on django middleware: http://www.djangobook.com/en/1.0/chapter15/
"""

import traceback

from seattlegeni.common.util import log

class LogExceptionMiddleware(object):
  
  def process_exception(self, request, exception):
    log.critical("An unhandled exception resulted from a request: " + traceback.format_exc())
    
    # Returning None indicates that default exception handling should be done.
    return None
