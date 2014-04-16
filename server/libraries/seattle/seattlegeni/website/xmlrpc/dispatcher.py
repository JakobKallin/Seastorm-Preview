"""
<Program>
  dispatcher.py

<Started>
  6 July 2009

<Author>
  Justin Samuel

<Purpose>
  XMLRPC handler for django.

  Nothing in this file needs to be modified when adding/removing/changing
  public xmlrpc methods. For that, see the views.py file in the same directory.

  This xmlrpc dispatcher for django is modified from the version at:
  http://code.djangoproject.com/wiki/XML-RPC
"""

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse

from seattlegeni.website.xmlrpc.views import PublicXMLRPCFunctions
from django.views.decorators.csrf import csrf_exempt


# This is the url that will be displayed if the xmlrpc service is requested
# directory through a web browser (that is, through a GET request).
SEATTLECLEARINGHOUSE_XMLRPC_API_DOC_URL = "https://seattle.cs.washington.edu/wiki/SeattleGeniApi"

# Create a Dispatcher. This handles the calls and translates info to function maps.
# TODO: allow_none = True or False? Does using None in the api make the xmlrpc
#       api python-specific?
dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None)


@csrf_exempt
def rpc_handler(request):
  """
  All xmlrpc requests are initially routed here by django. The actual functions we
  implement are in the views.py file. This rpc_handler function will make sure that
  what we return from the functions in views.py will be turned into a valid xmlrpc
  response.
  
  If POST data is defined, it assumes it's XML-RPC and tries to process as such.
  If the POST data is empty or if it is a GET request, this assumes the request is
  from a browser and responds saying it's an xmlrpc service.
  
  This function does not need to be called from anywhere other than having it
  defined in urls.py. That is, you generally shouldn't need to ever use this
  function directly.
  """
  response = HttpResponse()
  if len(request.POST):
    response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
  else:
    response.write("<b>This is the SeattleGeni XML-RPC Service.</b><br>")
    response.write("Please see <a href=" + SEATTLECLEARINGHOUSE_XMLRPC_API_DOC_URL + ">" + SEATTLECLEARINGHOUSE_XMLRPC_API_DOC_URL + "</a> for more information.")

  response['Content-length'] = str(len(response.content))
  return response



# All methods in the PublicXMLRPCFunctions class will be available as xmlrpc functions.
dispatcher.register_instance(PublicXMLRPCFunctions())
