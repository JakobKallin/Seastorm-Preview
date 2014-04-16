# Modules to make available for convenience so the names are available in the
# ipython shell. Just a lazy way to not have to execute these lines individually
# in a new shell.
from seattlegeni.website.control import interface
from seattlegeni.common.api import backend
from seattlegeni.common.api import keydb
from seattlegeni.common.api import keygen
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb
from seattlegeni.common.api import nodemanager

# grab a few objects to play with
g = maindb.get_user('user0')
(v, v2) = maindb.get_available_wan_vessels(g, 2)[:2]

