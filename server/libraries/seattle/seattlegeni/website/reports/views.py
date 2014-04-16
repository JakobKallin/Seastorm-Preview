"""
<Program>
  views.py

<Started>
  September 4, 2009

<Author>
  Justin Samuel

<Purpose>
  Views for reports about seattlegeni.
"""

import django.contrib.auth.decorators
from django.http import HttpResponse

from seattlegeni.common.util import statistics






def user_is_staff_member(user):
  return user.is_authenticated() and user.is_staff





@django.contrib.auth.decorators.user_passes_test(user_is_staff_member)
def index(request):
  html = '<html><head><style>body { font-family : sans-serif; }</style></head><body>'
  html += '<h2>Available reports</h2>'
  html += 'Note: some of these reports are not generated efficiently. The ones '
  html += 'that take a long time to load are probably hammering the database.<br /><br />'
  html += '<ul>'
  html += '<li><a href="%s">%s</a></li>' % ("all", "All reports on one page") 
  html += '<li><a href="%s">%s</a></li>' % ("donations", "Donations")
  html += '<li><a href="%s">%s</a></li>' % ("acquired_vessels", "Acquired vessels")
  html += '<li><a href="%s">%s</a></li>' % ("vessels_by_port", "Available vessels by port")
  html += '<li><a href="%s">%s</a></li>' % ("lan_sizes_by_port", "Available LAN sizes by port")
  html += '</ul>'
  html += '</body></html>'
  return HttpResponse(html)





@django.contrib.auth.decorators.user_passes_test(user_is_staff_member)
def all(request):
  lines = []
  lines += _get_text_number_of_vessels_acquired_per_user()
  lines.append("")
  lines += _get_text_donations_per_user()
  lines.append("")
  lines += _get_text_available_vessels_by_port()
  lines.append("")
  lines += _get_text_lan_sizes_by_port()
  output = "\n".join(lines)
  return HttpResponse(output, content_type='text/plain')
  
  
  


@django.contrib.auth.decorators.user_passes_test(user_is_staff_member)
def acquired_vessels(request):
  output = "\n".join(_get_text_number_of_vessels_acquired_per_user())
  return HttpResponse(output, content_type='text/plain')
  
  



@django.contrib.auth.decorators.user_passes_test(user_is_staff_member)
def donations(request):
  output = "\n".join(_get_text_donations_per_user())
  return HttpResponse(output, content_type='text/plain')


  


@django.contrib.auth.decorators.user_passes_test(user_is_staff_member)
def vessels_by_port(request):
  output = "\n".join(_get_text_available_vessels_by_port())
  return HttpResponse(output, content_type='text/plain')





def lan_sizes_by_port(request):
  output = "\n".join(_get_text_lan_sizes_by_port())
  return HttpResponse(output, content_type='text/plain')

  



def _get_text_number_of_vessels_acquired_per_user():
  
  lines = []
  lines.append("Number of vessels acquired per user")
  lines.append("-----------------------------------")
  
  vessel_acquisition_dict = statistics.get_vessel_acquisition_counts_by_user()
  
  for username in vessel_acquisition_dict:
    lines.append(username + (" " * (25 - len(username))) + str(vessel_acquisition_dict[username]))
  
  lines.append("")
  lines.append("Vessel acquisition summary")
  lines.append("--------------------------")
  lines.append("There are " +  str(len(vessel_acquisition_dict.keys())) + " users who have acquired vessels.")
  lines.append("There are " + str(sum(vessel_acquisition_dict.values())) + " acquired vessels.")

  return lines





def _get_text_donations_per_user():
  
  lines = []
  lines.append("Donations per user")
  lines.append("------------------")
  
  donations_dict = statistics.get_donation_counts_by_user()
  
  lines.append("User" + (" " * (25 - len("User"))) + "Active" + "\t" + "Inactive")
  lines.append("----" + (" " * (25 - len("----"))) + "------" + "\t" + "--------")
    
  total_active_donations = 0
  total_inactive_donations = 0
    
  for username in donations_dict:
    (active_donation_count, inactive_donation_count) = donations_dict[username]
    total_active_donations += active_donation_count 
    total_inactive_donations +=  inactive_donation_count
    lines.append(username + (" " * (25 - len(username))) + str(active_donation_count) + "\t" + str(inactive_donation_count))

  lines.append("")
  lines.append("Donation summary")
  lines.append("--------------------------")
  lines.append("Total active donations:   " +  str(total_active_donations))
  lines.append("Total inactive donations: " +  str(total_inactive_donations))
  
  return lines

  

  
  
def _get_text_available_vessels_by_port():
  
  lines = []
  lines.append("Available vessels by port")
  lines.append("-------------------------")
  
  available_vessels_dict = statistics.get_available_vessel_counts_by_port()
  
  lines.append("%s\t%s\t%s\t%s" % ("Port", "All", "No-NAT", "Only-NAT"))
  lines.append("%s\t%s\t%s\t%s" % ("----", "---", "------", "--------"))
  
  for port in available_vessels_dict:
    portdict = available_vessels_dict[port]
    lines.append("%s\t%s\t%s\t%s" % (port, portdict["all"], portdict["no_nat"], portdict["only_nat"]))

  return lines





def _get_text_lan_sizes_by_port():
  
  lines = []
  lines.append("Available LAN sizes by port")
  lines.append("---------------------------")
  
  lan_sizes_by_port = statistics.get_available_lan_vessel_counts()
  
  lines.append("%s\t%s" % ("Port", "Size List (top five)"))
  lines.append("%s\t%s" % ("----", "--------------------"))
  
  for port in lan_sizes_by_port:
    size_list = lan_sizes_by_port[port][:5]
    lines.append("%s\t%s" % (port, size_list))

  return lines
