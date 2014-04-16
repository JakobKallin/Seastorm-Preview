"""
<Program>
  errorviews.py

<Started>
  August 4, 2008

<Author>
  Justin Samuel

<Purpose>
  This module defines functions used for rendering error pages. We don't use the
  default error views because we want our 500 error to have access to the
  MEDIA_URL setting and therefore look like the rest of the site.
  
  We don't define a handler for 404 errors because the default one passes a
  RequestContext already, so we don't need to customize it to be able to
  access the MEDIA_URL value in templates. The 404.html file will be used
  by the default 404handler.
"""


from django.template import loader, RequestContext
from django import http



def internal_error(request):
  """
  The view that is used for rendering internal errors.
  This view function is referenced in the 500handler variable in urls.conf.
  """
  template = loader.get_template('500.html')
  return http.HttpResponseServerError(template.render(RequestContext(request, {})))
