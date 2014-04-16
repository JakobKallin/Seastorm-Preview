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
original_dict = {
  'levelone':{'callback': nullfunction, 'help_text': 'Help 1', 'summary': 'Summary 1', 'children':{
      'leveltwo':{'callback': nullfunction, 'help_text': 'Help 2', 'summary': 'Summary 2', 'children':{}},
  }},
}



def rootlevel_test():
  level_one_dict = {
    'leveloneprime':{'callback': nullfunction, 'help_text': 'Help 1`', 'summary': 'Summary 1`', 'children':{}},
  }
  
  level_one_expected = {
    'levelone':{'callback': nullfunction, 'help_text': 'Help 1', 'summary': 'Summary 1', 'children':{
        'leveltwo':{'callback': nullfunction, 'help_text': 'Help 2', 'summary': 'Summary 2', 'children':{}},
    }},
    'leveloneprime':{'callback': nullfunction, 'help_text': 'Help 1`', 'summary': 'Summary 1`', 'children':{}},
  }
  
  testdict = deepcopy(original_dict)
  seash_modules.merge_commanddict(testdict, level_one_dict)
  if not seash_modules.are_cmddicts_same(testdict, level_one_expected):
    raise Exception("Failed to merge dictionaries on root level")
  
  # Repeat the same test the other way around
  testdict = deepcopy(level_one_dict)
  seash_modules.merge_commanddict(testdict, original_dict) 
  if not seash_modules.are_cmddicts_same(testdict, level_one_expected):
    raise Exception("Failed to merge dictionaries on root level")



def secondlevel_test():
  # Make sure merging on 2nd-level works
  level_two_dict = {
    'levelone':{'children':{
        'leveltwoprime':{'callback': nullfunction, 'help_text': 'Help 2`', 'summary': 'Summary 2`', 'children':{}},
    }},
  }
  
  level_two_expected = {
    'levelone':{'callback': nullfunction, 'help_text': 'Help 1', 'summary': 'Summary 1', 'children':{
        'leveltwo':{'callback': nullfunction, 'help_text': 'Help 2', 'summary': 'Summary 2', 'children':{}},
        'leveltwoprime':{'callback': nullfunction, 'help_text': 'Help 2`', 'summary': 'Summary 2`', 'children':{}},
    }},
  }
  
  testdict = deepcopy(original_dict)
  seash_modules.merge_commanddict(testdict, level_two_dict)
  if not seash_modules.are_cmddicts_same(testdict, level_two_expected):
    import pdb;
    pdb.set_trace()
    raise Exception("Failed to merge dictionaries on 2nd level")
  
  # Repeat the same test the other way around
  testdict = deepcopy(level_two_dict)
  seash_modules.merge_commanddict(testdict, original_dict) 
  if not seash_modules.are_cmddicts_same(testdict, level_two_expected):
    raise Exception("Failed to merge dictionaries on 2nd level")



rootlevel_test()
secondlevel_test()