"""
<Program>
  logrequest.py

<Started>
  6 July 2009

<Author>
  Justin Samuel

<Purpose>
  We register "middleware" with django to help of log requests, including being
  able to uniquely identify all future logging done as part of the same request.

  Documenation on django middleware: http://www.djangobook.com/en/1.0/chapter15/
"""


from seattlegeni.common.util import log

class LogRequestMiddleware(object):
  
  def process_request(self, request):
    # Leave the actual logging work to code in the log module.
    log.log_start_request(request)
    
    # Returning None indicates that the request should continue to be processed.
    return None
