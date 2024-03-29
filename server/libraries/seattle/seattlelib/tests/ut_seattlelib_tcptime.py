"""
<Purpose>
  Test the tcp_time library which now uses
  Repy V2 network API calls.
  Function Tested:
    tcp_time_updatetime() in ntp_time.repy
"""
from repyportability import *
add_dy_support(locals())

dy_import_module_symbols("tcp_time.repy")

    
from repyportability import *
add_dy_support(locals())

dy_import_module_symbols("tcp_time.repy")

try:
  time_updatetime(12345)

  time_gettime()

except TimeError, err:
  log("[FAILED]: TCP time failed for following reason: " + str(err))
