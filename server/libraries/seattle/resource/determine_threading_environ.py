
import nonportable

NORMAL_THREADS = str(500) # How many threads to report for Desktop systems
MINIMUM_THREADS = str(5)  # "" for Mobile Systems

# If we see more than this many processes, assume a desktop system
NON_MOBILE_THRES = 50

# Predetermine based on OS the suitability of using 500 threads
DESKTOP = ["Linux", "Darwin", "Windows"]
MOBILE = ["WindowsCE", "Unknown"]

ostype = nonportable.ostype

# If we are on linux, check if it is mobile, e.g. Nokia
if ostype == "Linux":
  try:
    # Try this command, see if we can determine the number of processes
    # ps ax should list all the processes running, and wc will tally them up
    cmd = "ps ax | wc -l"
  
    # Launch ps
    import subprocess
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
  
    # Get the output
    cmddata = proc.stdout.read()
    p.stdout.close()
  
    count = int(cmddata.strip())
  
    if count >= NON_MOBILE_THRES:
      print NORMAL_THREADS
    else:
      print MINIMUM_THREADS
    exit()
  
  except:
    # It is probably better to assume we are on a Desktop for Linux systems
    print NORMAL_THREADS
    exit()


# Check if this is a Desktop category
if ostype in DESKTOP:
  print NORMAL_THREADS
  

# Fall back onto mobile  
else:
  print MINIMUM_THREADS


