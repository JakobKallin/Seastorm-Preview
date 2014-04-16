#!/usr/bin/env python
"""
This script is used to output single lines of comma-separated data for graphing
statistics related to seattlegeni.

Usage:
  python print_data_point.py node_overview CURRENT_VERSION
  or
  python print_data_point.py node_type
  or
  python print_data_point.py vessels
  or
  python print_data_point.py advertise

  When using the 'node_overview' option, you have to pass an extra argument of
  the current version of seattlegeni. For example:
    python print_data_point.py node_overview 0.1n

All of the usages print out something like this, just one single line:

2009-10-29 14:30,472,3

The above is a date (2009-10-29 14:30), followed by two numbers (472 and 3).
"""

from seattlegeni.website.control.models import Node
from seattlegeni.website.control.models import Vessel
from seattlegeni.website import settings

from seattlegeni.common.api import maindb

import datetime
import sys

# Import necessary repy files
from seattle.repyportability import *
add_dy_support(locals())

dy_import_module_symbols("rsa.repy")
dy_import_module_symbols("advertise.repy")

# This is the v2.publickey, the key is advertised by every single node manager thats up and running.
v2key = {'e': 22599311712094481841033180665237806588790054310631222126405381271924089573908627143292516781530652411806621379822579071415593657088637116149593337977245852950266439908269276789889378874571884748852746045643368058107460021117918657542413076791486130091963112612854591789518690856746757312472362332259277422867L, 'n': 12178066700672820207562107598028055819349361776558374610887354870455226150556699526375464863913750313427968362621410763996856543211502978012978982095721782038963923296750730921093699612004441897097001474531375768746287550135361393961995082362503104883364653410631228896653666456463100850609343988203007196015297634940347643303507210312220744678194150286966282701307645064974676316167089003178325518359863344277814551559197474590483044733574329925947570794508677779986459413166439000241765225023677767754555282196241915500996842713511830954353475439209109249856644278745081047029879999022462230957427158692886317487753201883260626152112524674984510719269715422340038620826684431748131325669940064404757120601727362881317222699393408097596981355810257955915922792648825991943804005848347665699744316223963851263851853483335699321871483966176480839293125413057603561724598227617736944260269994111610286827287926594015501020767105358832476708899657514473423153377514660641699383445065369199724043380072146246537039577390659243640710339329506620575034175016766639538091937167987100329247642670588246573895990251211721839517713790413170646177246216366029853604031421932123167115444834908424556992662935981166395451031277981021820123445253L}




def main():
  arg_to_func_dict = {"node_overview" : get_node_overview_line, 
                      "node_type": get_node_type_line, 
                      "vessels" : get_vessels_line,
                      "advertise" : get_advertise_line}
    
  if len(sys.argv) < 2 or sys.argv[1] not in arg_to_func_dict:
    print "Usage: print_data_points.py [" + "|".join(arg_to_func_dict.keys()) + "] (possible other args)" 
    sys.exit(1)

  print arg_to_func_dict[sys.argv[1]]()





def _datestr():
  date = datetime.datetime.now()
  return "%d-%02d-%02d %02d:%02d" % (date.year, date.month, date.day,
                                     date.hour, date.minute)





def get_node_overview_line():
  parts = []
  parts.append(_datestr())
  parts.append(str(_active_node_count()))
  parts.append(str(_active_broken_node_count()))
  parts.append(str(_active_old_version_node_count()))
  return ",".join(parts)


def _active_node_count():
  return len(maindb.get_active_nodes())


def _active_broken_node_count():
  return len(maindb.get_active_nodes_include_broken()) - len(maindb.get_active_nodes())


def _active_old_version_node_count():
  currentversion = sys.argv[2]
  queryset = Node.objects.filter(is_active=True, is_broken=False)
  queryset = queryset.exclude(last_known_version=currentversion)
  return queryset.count()





def get_node_type_line():
  parts = []
  parts.append(_datestr())
  parts.append(str(_active_non_nat_node_count()))
  parts.append(str(_active_nat_node_count()))
  return ",".join(parts)


def _active_non_nat_node_count():
  queryset = Node.objects.filter(is_active=True, is_broken=False)
  queryset = queryset.exclude(last_known_ip__startswith=maindb.NAT_STRING_PREFIX)
  return queryset.count()


def _active_nat_node_count():
  queryset = Node.objects.filter(is_active=True, is_broken=False)
  queryset = queryset.filter(last_known_ip__startswith=maindb.NAT_STRING_PREFIX)
  return queryset.count()





def get_vessels_line():
  parts = []
  parts.append(_datestr())
  parts.append(str(_free_vessels()))
  parts.append(str(_acquired_vessels()))
  parts.append(str(_dirty_vessels()))
  return ",".join(parts)


def _free_vessels():
  queryset = Vessel.objects.filter(acquired_by_user=None)
  queryset = queryset.filter(node__is_active=True, node__is_broken=False)
  return queryset.count()


def _acquired_vessels():
  queryset = Vessel.objects.exclude(acquired_by_user=None)
  queryset = queryset.exclude(date_expires__lte=datetime.datetime.now())
  return queryset.count()


def _dirty_vessels():
  return len(maindb.get_vessels_needing_cleanup())



def _state_key_file_to_publickey(key_file_name):
  """ Retrieve pubkey from file and return the dictionary form of key"""
  return rsa_file_to_publickey(os.path.join(settings.SEATTLECLEARINGHOUSE_STATE_KEYS_DIR, key_file_name))



def get_advertise_line():
  """
  <Purpose>
    Lookup the nodes with their transition state key in order
    to find out how many nodes are in each state. Then print the
    number of nodes that are in each state.

  <Arguments>
    None

  <Exception>
    None

  <Side Effects>
    None
  
  <Return>
    None
  """

  state_keys = {"canonical" : _state_key_file_to_publickey("canonical.publickey"),
                "acceptdonation" : _state_key_file_to_publickey("acceptdonation.publickey"),
                "movingto_onepercentmanyevents" : _state_key_file_to_publickey("movingto_onepercentmanyevents.publickey"),
                "onepercent_manyevents" : _state_key_file_to_publickey("onepercentmanyevents.publickey")}

 
  parts = []
  parts.append(_datestr())
  parts.append(str(_lookup_nodes(state_keys["acceptdonation"])))
  parts.append(str(_lookup_nodes(state_keys["canonical"])))
  parts.append(str(_lookup_nodes(state_keys["movingto_onepercentmanyevents"])))
  parts.append(str(_lookup_nodes(state_keys["onepercent_manyevents"])))
  parts.append(str(_lookup_nodes(v2key)))
  return ",".join(parts)


def _lookup_nodes(node_state_pubkey):
  """
  <Purpose>
    Lookup nodes given a publickey.

  <Arguments>
    node_state_pubkey - publickey to use to lookup nodes.

  <Exception>
    Exception is printed to stderr.

  <Side Effects>
    None

  <Return>
    The number of nodes found using the public key.
  """

  # Lookup nodes using publickey.   If it timesout or fails, this is okay.  
  # just log it, return -1 (to print that in the log) and continue
  try:
    node_list = advertise_lookup(node_state_pubkey, maxvals = 10*1024*1024)
  except Exception, e:
    print >> sys.stderr, e
    return -1
  
  return len(node_list)


    
if __name__ == "__main__":
  main()
