"""
  <Program Name>
    Mac_BSD_resources.py

  <Started On>
    January 2009

  <Author>
    Carter Butaud
    Modified by Steven Portzer

  <Purpose>
    Runs ons a Mac or BSD system to benchmark important resources.

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
  
"""


import subprocess
import re
#import bandwidth
import measure_random
import measuredisk

def getShellPipe(cmd):
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout

def measure_resources():
    
  # First, get number of CPUs
  # SP: None is now reserved for unimplemented tests, and to differentiate
  # failed tests we return a string describing the error. At least in theory
  # this makes it easier to figure out what occurred.
  num_cpu = "unable to find number of CPUs"
  pipe = getShellPipe("sysctl hw.ncpu")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      num_cpu = int(line_s[1])
  pipe.close()

  # Next, get physical memory (RAM)
  phys_mem = "unable to find size of physical memory"
  pipe = getShellPipe("sysctl hw.physmem")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      phys_mem = int(line_s[1])
  pipe.close()

  """ 
  Anthony - this gives an answer much larger than what 
  can really be achieved. Rewriting to use ulimit instead.
  
  # Get max files open, defaulting to 1000
  # Make sure that 10% of the total system
  # is not more than the per process limit
  files_open = 1000
  files_open_per_proc = False
  files_open_total = False
  pipe = getShellPipe("sysctl kern.maxfiles")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      files_open_total = int(line_s[1])
  pipe.close()
  pipe = getShellPipe("sysctl kern.maxfilesperproc")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      files_open_per_proc = int(line_s[1])
  pipe.close()
  
  if files_open_per_proc and files_open_total:
    files_open = min(files_open_per_proc * 10, files_open_total)
  elif files_open_per_proc:
    files_open = 10 * files_open_per_proc
  elif files_open_total:
    files_open = files_open_total
  """
  # The ulimit command should only return a single value
  # for the max number of files open at a single time.
  pipe = getShellPipe("ulimit -n")
  for line in pipe:
    try:
      files_open = int(line)
    except ValueError:
      files_open = "bad value for max number of open files: " + str(line)


  # Get hard drive space
  disk_space = "unable to find hard drive size"
  pipe = getShellPipe("df -k .")
  seenFirstLine = False
  for line in pipe:
    if seenFirstLine:  
      line_s = re.split("\\s*", line)
      if len(line_s) >= 6 and line:
        disk_space = (int(line_s[3])) * 1024
    else:
      seenFirstLine = True
  pipe.close()

  # Get the max number of processes
  events = "unable to find max number of processes"
  pipe = getShellPipe("sysctl kern.maxprocperuid")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      events = int(line_s[1])
  pipe.close()

  # Get the max number of sockets
  maxsockets = "unable to find max number of sockets"
  pipe = getShellPipe("sysctl kern.ipc.maxsockets")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      maxsockets = int(line_s[1])
  pipe.close()
  
  if not isinstance(maxsockets, basestring):
    insocket = maxsockets / 2
    outsocket = maxsockets / 2
  else:
    insocket = maxsockets
    outsocket = maxsockets

  # Get the available bandwidth, defaulting to 100000
  """my_bandwidth = 100000
  server_ip = "128.208.1.137"
  try:
    my_bandwidth = bandwidth.get_bandwidth(server_ip)
  except:
    pass"""

  # SP: Measure random number generation rate, should work on all systems now
  try:
    random_max = measure_random.measure_random()
  except measure_random.InvalidTimeMeasurementError, e:
    random_max = str(e)
  

  # Measure the disk read write rate
  try:
    filewrite, fileread = measuredisk.main()
  except Exception, e:
    filewrite, fileread = str(e), str(e)

  resource_dict = {}

  resource_dict["cpu"] = num_cpu
  resource_dict["memory"] = phys_mem
  resource_dict["diskused"] = disk_space
  # benchmark_resources set a hard value of 500 for ever OS
  resource_dict["events"] = None # events
  resource_dict["filesopened"] = files_open
  resource_dict["insockets"] = insocket
  resource_dict["outsockets"] = outsocket
  resource_dict["random"] = random_max
  resource_dict["filewrite"] = filewrite
  resource_dict["fileread"] = fileread
  #print "resource netsend", my_bandwidth
  #print "resource netreceive", my_bandwidth
  
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
