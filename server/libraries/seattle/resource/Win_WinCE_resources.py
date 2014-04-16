"""
<Program Name>
  Linux_resources.py

<Started>
  January 18, 2009

<Author>
  Armon Dadgar
  Modified by Anthony Honstain
  Modified by Steven Portzer

<Return value notes>
  The dictionary returned by measure_resources() is used by
  benchmark_resources.py and contains a value for every system resource.
  If the system resource is successfully measured, then the measured value
  of that resource is returned as an integer. If a test fails, then a
  string describing the failure is returned for that resource. If the
  resource is not currently being measured, then None is returned.

  Formerly, None was returned for both failed and unimplemented tests, but
  this made it impossible to determine whether a benchmark had actually
  failed or if it was simply not being measured.

<Resource events>
  WARNING the 'events' resource is hardcoded to a value of 500
  
  The 'events' resource has proven very difficult to measure across the
  different operating systems, and on some it is infeasible to measure.
  The decision has been made to take 500 events for the node
  
  see benchmark_resources for more information.

<Armon's Notes>
  Generates some resource info for Windows and Windows Mobile

  Windows Mobile Info

  CPU's: 1
  Max Processes: 32
  Max Threads: Bound by Memory, default is 1 meg per tread, so 32 max
  This would essentially leave no memory for anything else, so lets do 1/4
  See: http://msdn.microsoft.com/en-us/library/bb202727.aspx
  Max Memory: Windows Mobile 5 limit is 32 megs per app
  Mobile 6 is 1 gig, but lets play it safe
  http://www.addlogic.se/articles/articles/windows-ce-6-memory-architecture.html
  I can't find a handle limit for Mobile, but lets just use 1/4 of desktop (50)
  Windows Mobile 6 has a 64K handle limit (system wide)

  Windows Info
  CPU's: %NUMBER_OF_PROCESSORS%
  Processes: I think I remember 32K
  Threads: 512 default, we will probably hit a memory limit first so...
  Lets do 1/4 of this, times the number of CPU's
  http://msdn.microsoft.com/en-us/library/ms684957.aspx
  Max Memory: 4 gigs on 32bit, but getMem info can handle up to 64 gig for 64bit machines
  64 sockets per app by default, see: http://msdn.microsoft.com/en-us/library/aa923605.aspx

  See: http://support.microsoft.com/kb/327699
  Total user objects can be between 200 and 18K per proc
  System limit of 64K
  See: http://msdn.microsoft.com/en-us/library/ms725486(VS.85).aspx
  So, lets use the lowest possible to play it safe
  64 sockets per app by default, see: http://msdn.microsoft.com/en-us/library/ms739169(VS.85).aspx

  libc._getmaxstdio() gives us the maximum number of file handles

  Loopback is a special case of network, we can do the same benchmark with a local addr

  
"""

import windows_api
import ctypes # Used to query for max file handles
import measure_random
import measuredisk

def measure_resources():

  # Get disk info, using current directory
  diskInfo = windows_api.disk_util(None)
  totalDisk = diskInfo["total_bytes"]
  freeDisk = diskInfo["freeBytes"]
  
  # Get meminfo
  memInfo = windows_api.global_memory_info()
  totalMem = memInfo["totalPhysical"]

  # Default to None, for WinCE
  numCPU = None

  import subprocess

  cmd="echo %NUMBER_OF_PROCESSORS%"
  try:
    proc=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    proc.stdout.close()
  except Exception, e:
    # SP: if something goes wrong, return a string giving some information
    # on what happened. The None return value is reserved for tests that
    # aren't implemented.
    numCPU = "unable to read number of processors: " + str(e)
  else:
    # Attempt to parse output for a number of CPU's
    try:
      num=int(output)
    except ValueError:
      numCPU = "bad value for number of processors: " + str(output)
    else:
      if num >= 1:
        numCPU = num
      else:
        numCPU = "non-positive value returned for number of processors: " \
                    + str(num)

  # Hard limit at 512
  # Anthony, we will have a default for all systems because
  # of the problems with measuring, using None here will trigger
  # the default in benchmark_resources.py .
  # threadMax = min(128*numCPU,512)
  threadMax = None

  libc = ctypes.cdll.msvcrt  
  handleMax = libc._getmaxstdio() # Query C run-time for maximum file handles

  # Anthony - we have chosen to use the default limit except for mobile
  # using None for socketMax here will trigger the default in 
  # benchmark_resources.py .
  socketMax = None

  # Measure random
  # SP: This test should now work on all systems. For failed tests, a string
  # describing the failure will be returned.
  try:
    randomMax = measure_random.measure_random()
  except measure_random.InvalidTimeMeasurementError, e:
    randomMax = str(e)


  # Measure the disk read write rate
  try:
    filewrite, fileread = measuredisk.main()
  except Exception, e:
    filewrite, fileread = str(e), str(e)



  resource_dict = {}

  resource_dict["cpu"] = numCPU
  resource_dict["memory"] = totalMem
  resource_dict["diskused"] = freeDisk

# The following are more per-process things
  resource_dict["events"] = threadMax
  resource_dict["filesopened"] = handleMax
  # The socketMax is split between in and out already.
  resource_dict["insockets"] = socketMax
  resource_dict["outsockets"] = socketMax
  resource_dict["random"] = randomMax
  resource_dict["filewrite"] = filewrite
  resource_dict["fileread"] = fileread

  # These resources are not measure in this script so a None
  # value is used to indicate it was not measured. 
  resource_dict["netrecv"] = None
  resource_dict["netsend"] = None
  resource_dict["lograte"] = None
  resource_dict["loopsend"] = None
  resource_dict["looprecv"] = None


  return resource_dict


if __name__ == "__main__":
  dict = measure_resources()

  print "resource cpu ", dict['cpu']
  print "resource memory ", dict['memory'], '\t', dict['memory'] / 1073741824.0, "GB"
  print "resource diskused ", dict['diskused'], '\t', dict['diskused'] / 1073741824.0, "GB"
  print "resource events ", dict['events']
  print "resource filesopened ", dict['filesopened']
  print "resource insockets ", dict['insockets']
  print "resource outsockets ", dict['outsockets']
  print "resource random ", dict['random'], '\t', dict['random'] / 11048576.0, "MB"
  print "resource filewrite ", dict['filewrite'], '\t', dict['filewrite'] / 1048576.0, "MB"
  print "resource fileread ", dict['fileread'], '\t', dict['fileread'] / 1048576.0, "MB"
  print "resource netrecv ", dict["netrecv"]
  print "resource netsend ", dict["netsend"]
  print "resource lograte ", dict["lograte"]
  print "resource loopsend ", dict["loopsend"]
  print "resource looprevc ", dict["looprecv"]
