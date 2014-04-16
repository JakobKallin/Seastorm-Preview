"""
<Program>
  assertions.py

<Started>
  29 June 2009

<Author>
  Justin Samuel

<Purpose>
  This is a utility module to provide simple assert_* functions which throw a
  AssertionError if the assertion fails. This is mostly intended to provide
  simple type checking of arguments to functions where the programmer calling
  the function should have been sure to provide the correct type of data.
  
  Note: We define __all__ at the bottom of this script to make sure that we
  only export the assertions we've defined here, not anything else that may be
  imported or used in this module. Only names that start with "assert_" are
  exported.
  
  Note: AssertionError is a python built-in exception.
"""

from seattlegeni.website.control.models import Donation
from seattlegeni.website.control.models import GeniUser
from seattlegeni.website.control.models import Node
from seattlegeni.website.control.models import Vessel



def assert_str(value):
  """
  <Purpose>
    Ensure that value is a string (can be str or unicode).
  """
  # Check for basestring which is the superclass of str and unicode.
  if not isinstance(value, basestring):
    raise AssertionError("Expected string value, received " + str(type(value)))



def assert_str_or_none(value):
  """
  <Purpose>
    Ensure that value is a string (can be str or unicode) or None.
  """
  # Check for basestring which is the superclass of str and unicode.
  if not isinstance(value, basestring) and value is not None:
    raise AssertionError("Expected string value or None, received " + str(type(value)))



def assert_int(value):
  """
  <Purpose>
    Ensure that value is an integer (can be int or long).
  """
  if not isinstance(value, int) and not isinstance(value, long):
    raise AssertionError("Expected int or long value, received " + str(type(value)))



def assert_positive_int(value):
  """
  <Purpose>
    Ensure that value is an integer (can be int or long) and is greater than
    zero.
  """
  if not isinstance(value, int) and not isinstance(value, long):
    raise AssertionError("Expected int or long value, received " + str(type(value)))
  if value < 1:
    raise AssertionError("Expected a positive value, received: " + str(value))



def assert_bool(value):
  """
  <Purpose>
    Ensure that value is a boolean.
  """
  if not isinstance(value, bool):
    raise AssertionError("Expected bool value, received " + str(type(value)))



def assert_list(value):
  """
  <Purpose>
    Ensure that value is a list.
  """
  if not isinstance(value, list):
    raise AssertionError("Expected list value, received " + str(type(value)))



def assert_list_of_str(value):
  """
  <Purpose>
    Ensure that value is a list of strings.
  """
  assert_list(value)
  for item in value:
    assert_str(item)



def assert_donation(value):
  """
  <Purpose>
    Ensure that value is a Donation object.
  """
  if not isinstance(value, Donation):
    raise AssertionError("Expected Donation object, received " + str(type(value)))



def assert_geniuser(value):
  """
  <Purpose>
    Ensure that value is a GeniUser object.
  """
  if not isinstance(value, GeniUser):
    raise AssertionError("Expected GeniUser object, received " + str(type(value)))
  


def assert_node(value):
  """
  <Purpose>
    Ensure that value is a Node object.
  """
  if not isinstance(value, Node):
    raise AssertionError("Expected Node object, received " + str(type(value)))
  


def assert_vessel(value):
  """
  <Purpose>
    Ensure that value is a Vessel object.
  """
  if not isinstance(value, Vessel):
    raise AssertionError("Expected Vessel object, received " + str(type(value)))
  


# Many modules are using the line 'from seattlegeni.common.util.assertions import *'
# to import the assertions. We define __all__ so that we only export names from
# this module that start with the "assert_". This prevents us from exporting anything
# we happened to import as well as any non-private helper functions that may get
# defined. 
__all__ = []
for name in dir():
  if name.startswith("assert_"):
    __all__.append(name)

