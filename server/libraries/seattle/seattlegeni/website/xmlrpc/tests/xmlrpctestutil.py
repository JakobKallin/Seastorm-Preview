"""
Based on:
  http://www.technobabble.dk/2008/apr/02/xml-rpc-dispatching-through-django-test-client/

With the addition of the following to make it work:
  self._use_datetime = False
"""

# We import the testlib FIRST, as the test db settings 
# need to be set before we import anything else.
from seattlegeni.tests import testlib

import cStringIO
import xmlrpclib

from django.test.client import Client

class TestTransport(xmlrpclib.Transport):
  """Handles connections to XML-RPC server through Django test client."""

  def __init__(self, *args, **kwargs):
    self.client = Client()

  def request(self, host, handler, request_body, verbose=0):
    self.verbose = verbose
    self._use_datetime = False
    response = self.client.post(handler,
                                request_body,
                                content_type="text/xml")
    res = cStringIO.StringIO(response.content)
    res.seek(0)
    return self.parse_response(res)
