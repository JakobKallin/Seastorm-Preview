import inspect
import sys
# No real preference for minimock, just the first one I used that did what
# I needed.
from minimock import Mock

def mock_module(module_name):
  """
  Replaces all of the functions of a module with mock versions of the same
  functions that don't do anything. Doesn't modify classes or the methods
  of classes, nor does it change any global data in the modules.
  
  Example usage:
    mock_module('seattlegeni.common.api.lockserver')
  """
  __import__(module_name)
  module = sys.modules[module_name]
  for item_name in dir(module):
    obj = getattr(module, item_name)
    if inspect.isfunction(obj):
      print "Mocking: " + module_name + "." + item_name
      setattr(module, item_name, Mock(obj))
