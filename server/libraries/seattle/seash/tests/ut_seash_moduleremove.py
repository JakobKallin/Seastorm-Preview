"""
Test the merging of commanddicts.

"""
# Needed so that the built-in type function is restored to the python
# abc library
import seash_dictionary

import seash_modules
from copy import deepcopy


def nullfunction():
  """ We need to point the callback to an existing function. """
  pass


# Base dictionary that we will make a copy of and run the tests on.
COMBINED_DICT = {
  'show':{'callback': nullfunction, 'help_text': 'Help show', 'summary': 'Summary show', 'children':{
      'x':{'callback': nullfunction, 'help_text': 'Help show x', 'summary': 'Summary show x', 'children':{
      }},
      'y':{'callback': nullfunction, 'help_text': 'Help show y', 'summary': 'Summary show y', 'children':{
      }},
  }},
  'get':{'callback': nullfunction, 'help_text': 'Help get', 'summary': 'Summary get', 'children':{
      'x':{'callback': nullfunction, 'help_text': 'Help get x', 'summary': 'Summary get x', 'children':{
      }},
      'y':{'callback': nullfunction, 'help_text': 'Help get y', 'summary': 'Summary get y', 'children':{
      }},
  }},
}

# This dictionary contains all the get-commands.
GET_DICT = {
  'get':{'callback': nullfunction, 'help_text': 'Help get', 'summary': 'Summary get', 'children':{
      'x':{'callback': nullfunction, 'help_text': 'Help get x', 'summary': 'Summary get x', 'children':{
      }},
      'y':{'callback': nullfunction, 'help_text': 'Help get y', 'summary': 'Summary get y', 'children':{
      }},
  }},
}

# This dictionary contains all the show-commands.
SHOW_DICT = {'show':{'callback': nullfunction, 'help_text': 'Help show', 'summary': 'Summary show', 'children':{
      'x':{'callback': nullfunction, 'help_text': 'Help show x', 'summary': 'Summary show x', 'children':{
      }},
      'y':{'callback': nullfunction, 'help_text': 'Help show y', 'summary': 'Summary show y', 'children':{
      }},
  }},
}


# This dictionary contains all the show-commands.
SHOW_X_DICT = {'show':{'children':{
      'x':{'callback': nullfunction, 'help_text': 'Help show x', 'summary': 'Summary show x', 'children':{
      }},
  }},
}

# This dictionary contains all the show-commands.
SHOW_DEFINED_Y_DICT = {'show':{'callback': nullfunction, 'help_text': 'Help show', 'summary': 'Summary show', 'children':{
      'y':{'callback': nullfunction, 'help_text': 'Help show y', 'summary': 'Summary show y', 'children':{
      }},
  }},
}



def branch_test():  
  testdict = deepcopy(COMBINED_DICT)
  seash_modules.remove_commanddict(testdict, SHOW_DICT)
  
  if not seash_modules.are_cmddicts_same(testdict, GET_DICT):
    raise Exception("Failed to remove entire command branch GET")
  
  # Repeat the same test the other way around
  testdict = deepcopy(COMBINED_DICT)
  seash_modules.remove_commanddict(testdict, GET_DICT)
  
  if not seash_modules.are_cmddicts_same(testdict, SHOW_DICT):
    raise Exception("Failed to remove entire command branch SHOW")



def singlecommand_test():
  # Removing a child node when there are other siblings must not have
  # affect the other siblings
  testdict = deepcopy(SHOW_DICT)
  seash_modules.remove_commanddict(testdict, SHOW_X_DICT)
  
  if not seash_modules.are_cmddicts_same(testdict, SHOW_DEFINED_Y_DICT):
    raise Exception("Failed to remove child node")
  
  # When removing a child node with a parent definition when there are other 
  # siblings, we should remove the parent definition as well. 
  testdict = deepcopy(SHOW_DICT)
  seash_modules.remove_commanddict(testdict, SHOW_DEFINED_Y_DICT)
  
  if not seash_modules.are_cmddicts_same(testdict, SHOW_X_DICT):
    raise Exception("Failed to remove parent node definition when removing child node")



singlecommand_test()
branch_test()