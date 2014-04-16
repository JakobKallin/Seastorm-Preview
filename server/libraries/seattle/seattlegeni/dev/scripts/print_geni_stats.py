#!/usr/bin/env python
"""
Print a summarization of the status of seattlegeni, according to information in
the database.
"""

from seattlegeni.common.util import statistics






if __name__ == "__main__":
  
  # Decrease the amount of logging output.
  from seattlegeni.common.util import log
  log.loglevel = log.LOG_LEVEL_CRITICAL
  
  
  
  print "Available vessels by port"
  print "-------------------------"
  
  available_vessels_dict = statistics.get_available_vessel_counts_by_port()
  
  print "%s\t%s\t%s\t%s" % ("Port", "All", "No-NAT", "Only-NAT")
  print "%s\t%s\t%s\t%s" % ("----", "---", "------", "--------")
  
  for port in available_vessels_dict:
    portdict = available_vessels_dict[port]
    print "%s\t%s\t%s\t%s" % (port, portdict["all"], portdict["no_nat"], portdict["only_nat"])



  print
  print "Number of vessels acquired per user"
  print "-----------------------------------"
  
  vessel_acquisition_dict = statistics.get_vessel_acquisition_counts_by_user()
  
  for username in vessel_acquisition_dict:
    print username + (" " * (25 - len(username))) + str(vessel_acquisition_dict[username])
  
  print
  print "Vessel acquisition summary"
  print "--------------------------"
  print "There are " +  str(len(vessel_acquisition_dict.keys())) + " users who have acquired vessels."
  print "There are " + str(sum(vessel_acquisition_dict.values())) + " acquired vessels."



  print
  print "Donations per user"
  print "------------------"
  
  donations_dict = statistics.get_donation_counts_by_user()
  
  print "User" + (" " * (25 - len("User"))) + "Active" + "\t" + "Inactive"
  print "----" + (" " * (25 - len("----"))) + "------" + "\t" + "--------"
    
  total_active_donations = 0
  total_inactive_donations = 0
    
  for username in donations_dict:
    (active_donation_count, inactive_donation_count) = donations_dict[username]
    total_active_donations += active_donation_count 
    total_inactive_donations +=  inactive_donation_count
    print username + (" " * (25 - len(username))) + str(active_donation_count) + "\t" + str(inactive_donation_count)

  print
  print "Donation summary"
  print "--------------------------"
  print "Total active donations:   " +  str(total_active_donations)
  print "Total inactive donations: " +  str(total_inactive_donations)

