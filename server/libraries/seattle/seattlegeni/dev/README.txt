The scripts and mock utilities in this directory are just for convenience
during development right now. They aren't clean enough, structured enough,
or documented well enough to be anything more than that. Hopefully they
will grow into more general testing and monitoring tools.

Some of them are things I've only used from an ipython shell.

Example of using ipython to do manual testing
---------------------------------------------

Note: You'll need the minimock package installed to run the following
example exactly as shown.

First, set your environment variables:

  export PYTHONPATH=$PYTHONPATH:/path/to/trunk
  export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'
  
Change to this directory:

  cd trunk/seattlegeni/dev/

Populate the database with some data (assumes you've run
./manage.py syncdb already, or ./manage.py flush to clean out
the data from a database you previously had test data in):

  python scripts/populate_database_1.py
  
Possibly check to see what your database contains, e.g.:

  python scripts/get_geni_stats.py

Now start an ipython shell and play around:

  ipython

In [1]: run ipython/prep1.py

In [2]: run mock/lockserver.py
Mocking: seattlegeni.common.api.lockserver._assert_valid_lockserver_handle
Mocking: seattlegeni.common.api.lockserver._perform_lock_request          
Mocking: seattlegeni.common.api.lockserver.create_lockserver_handle       
Mocking: seattlegeni.common.api.lockserver.destroy_lockserver_handle      
Mocking: seattlegeni.common.api.lockserver.lock_multiple_nodes            
Mocking: seattlegeni.common.api.lockserver.lock_multiple_users            
Mocking: seattlegeni.common.api.lockserver.lock_node                      
Mocking: seattlegeni.common.api.lockserver.lock_user                      
Mocking: seattlegeni.common.api.lockserver.log_function_call              
Mocking: seattlegeni.common.api.lockserver.unlock_multiple_nodes          
Mocking: seattlegeni.common.api.lockserver.unlock_multiple_users          
Mocking: seattlegeni.common.api.lockserver.unlock_node                    
Mocking: seattlegeni.common.api.lockserver.unlock_user                    

In [3]: run mock/unreliablebackend.py
Mocking: seattlegeni.common.api.backend.acquire_vessel

In [4]: geniuser = maindb.get_user('user0')
[24/Jul/2009 15:43:08] INFO - Calling: get_user (module seattlegeni.common.api.maindb), args: ('user0',), kwargs: ().
[24/Jul/2009 15:43:08] INFO - Returning from get_user: GeniUser:user0                                                

In [5]: interface.acquire_vessels(geniuser, 1, 'rand')
[24/Jul/2009 15:43:17] INFO - Calling: acquire_vessels (module seattlegeni.website.control.interface), args: (<GeniUser: GeniUser:user0>, 1, 'rand'), kwargs: ().                                                                                                                                               
Called <function create_lockserver_handle at 0x8f531b4>()                                                                                               
Called <function lock_user at 0x8f53224>(None, u'user0')                                                                                                
[24/Jul/2009 15:43:17] INFO - Calling: get_user (module seattlegeni.common.api.maindb), args: (u'user0',), kwargs: ().                                  
[24/Jul/2009 15:43:17] INFO - Returning from get_user: GeniUser:user0                                                                                   
...snip...
[24/Jul/2009 15:43:18] INFO - Returning from get_node_identifier_from_vessel: node7
Called <function lock_node at 0x8f53304>(None, u'node7')
[24/Jul/2009 15:43:18] INFO - Calling: record_acquired_vessel (module seattlegeni.common.api.maindb), args: (<GeniUser: GeniUser:user0>, <Vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7>), kwargs: ().
[24/Jul/2009 15:43:18] INFO - Returning from record_acquired_vessel: None
Called <function unlock_node at 0x8f5333c>(None, u'node7')
[24/Jul/2009 15:43:18] INFO - Returning from _do_acquire_vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7
[24/Jul/2009 15:43:18] INFO - Returning from _acquire_vessels_from_list: [<Vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7>]
[24/Jul/2009 15:43:18] INFO - Returning from acquire_rand_vessels: [<Vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7>]
Called <function unlock_user at 0x8f5325c>(None, u'user0')
Called <function destroy_lockserver_handle at 0x8f531ec>(None)
[24/Jul/2009 15:43:18] INFO - Returning from acquire_vessels: [<Vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7>]
Out[5]: [<Vessel: Vessel:[Node:node7:127.0.0.1:1234]:v7>]
