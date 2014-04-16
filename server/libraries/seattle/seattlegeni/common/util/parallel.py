"""
<Program>
  parallel.py

<Started>
  14 August 2009

<Author>
  Justin Samuel

<Purpose>
  This module just provides a convenience function for using the repy
  parallelize module for parallelizing a function call. This is just to
  keep other code clean and prevent accidental leakage of the handles
  provided by the repy module for parallelized function.
"""

import time
import traceback

from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("parallelize.repy")





# The number of threads to be running at a given time for each parallelized
# function call.
CONCURRENT_THREADS_PER_CALL = 10





def run_parallelized(first_arg_list, func, *additional_args):
  """
   <Purpose>
      Call a function with each argument in a list in parallel.
   <Arguments>
      first_arg_list:
          The list of arguments the function should be called with. Each
          argument is passed once to the function.
      func:
          The function to call
      additional_args:
          Extra arguments the function should be called with (every function
          is passed the same extra args).
   <Exceptions>
      InternalError
        If running the parallelized function failed (failed to run at all, not
        just had each function call raise an exception).
   <Side Effects>
      Creates multiple threads to run func in parallel.
   <Returns>
      A dictionary with the results.   The format is
        {'exception':list of tuples with (target, exception string), 
         'aborted':list of targets, 'returned':list of tuples with (target, 
         return value)}
  """
  
  try:
    phandle = parallelize_initfunction(first_arg_list, func, CONCURRENT_THREADS_PER_CALL, *additional_args)
  
    try: 
      while not parallelize_isfunctionfinished(phandle):
        time.sleep(0.1)
  
      return parallelize_getresults(phandle)
  
    finally:
      # clean up the handle
      parallelize_closefunction(phandle)
      
  except ParallelizeError, e:
    raise InternalError("Failed to run parallelized function: " + traceback.format_exc())
