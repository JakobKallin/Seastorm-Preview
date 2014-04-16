= Deploying and running SeattleGeni =

  * Do initial preparation:

    * Install django 1.1+. http://docs.djangoproject.com/en/dev/topics/install/

    * Checkout the seattle trunk from svn.
  
    * Deploy all necessary files to a directory of your choice. The directory
      you deploy to should be the name of a directory that does not yet exist.
      For example:
    
      python ./trunk/seattlegeni/deploymentscripts/deploy_seattlegeni.py ./trunk /tmp/deploy
    
    * Change to the seattlegeni directory that is in the directory you deployed
      to. For example:
    
        cd /tmp/deploy/seattlegeni
    
      Note: all future steps/instructions will assume you are in this directory.

      
  * NOTE: starting all of the processes is simplified by using the script
    deploymentscripts/start_seattlegeni_components.sh. See the section on
    "Notes for Production" for more information. For reference, we'll explain
    here how to start the individual components as well as include first-time
    configuration information. Note that when starting these manually, you need
    to start them in the order shown. Most importantly, first the lockserver,
    then the backend, then everything else.


  * Start the website:

    * Create a mysql database for seattlegeni (e.g. called `seattlegeni`).
  
    * Edit website/settings.py and specify the name of the seattlegeni
      database, as well as the database username, password, etc.
      Also set a long, random string the value of SECRET_KEY.
    
      Note: using sqlite will not work for everything, but it should work for
      most things if that's more convenient during development.
      
    * If this is a production launch, set the following in website/settings.py
    
      # If DEBUG is True, then error details will be shown on the website and ADMINS
      # will not receive an email when an error occurs. So, this should be False in
      # production.
      DEBUG = False
      TEMPLATE_DEBUG = DEBUG
      
      # The directory where we keep the public keys of the node state keys.
      SEATTLECLEARINGHOUSE_STATE_KEYS_DIR = "path/to/statekeys"
      
      # The directory where the base installers named seattle_linux.tgz, seattle_mac.tgz,
      # and seattle_win.zip are located.
      SEATTLECLEARINGHOUSE_BASE_INSTALLERS_DIR = ""
      
      # The directory in which customized installers created by seattlegeni will be
      # stored. A directory within this directory will be created for each user.
      SEATTLECLEARINGHOUSE_USER_INSTALLERS_DIR = os.path.join(SEATTLECLEARINGHOUSE_BASE_INSTALLERS_DIR, "geni")

      # The url that corresponds to SEATTLECLEARINGHOUSE_USER_INSTALLERS_DIR
      SEATTLECLEARINGHOUSE_USER_INSTALLERS_URL = "https://hostname/dist/geni"
      
      # Email addresses of people that should be emailed when a 500 error occurs on
      # the site when DEBUG = False (that is, in production). Leave this to be empty
      # if nobody should receive an email. 
      ADMINS = (
        # ('Your Name', 'your_email@domain.com'),
      )
      
      # To be able to send mail to ADMINS when there is an error, django needs to
      # know about an SMTP server it can use. That info is defined here.
      EMAIL_HOST = 'smtp.gmail.com'
      EMAIL_HOST_USER = 'an.error.sending.account@gmail.com'
      EMAIL_HOST_PASSWORD = 'PASSWORD_HERE'
      EMAIL_PORT = 587
      EMAIL_USE_TLS = True
      
      # Email address that 500 error notifications will be sent from.
      SERVER_EMAIL = "error@seattlegeni.server.hostname"
      
    * Set your environment variables:

        export PYTHONPATH=$PYTHONPATH:/tmp/deploy:/tmp/deploy/seattle
        export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'
        
      Node: the /tmp/deploy path entry is to make available the two packages
      'seattlegeni' and 'seattle' which the deployment script created in the
      /tmp/deploy directory. The /tmp/deploy/seattle path item is to ensure
      that repyhelper (NOW OBSOLETE?) can find repy files in the python path, 
      as the repy files were placed in this directory by the deployment script.
    
    * Create the database structure:
  
        python website/manage.py syncdb
      
      You can use the following if you don't want to be prompted about creating
      an administrator account:
    
        python website/manage.py syncdb --noinput
   
    * For development, start the django development webserver:
  
        python website/manage.py runserver
      
      You will now have a local development server running on port 8000.
      
    * For production, setup to run through apache:
    
      TODO: add information on setting up to run through apache

      
  * Start the lockserver:
      
    * Set your environment variables:
  
        export PYTHONPATH=$PYTHONPATH:/tmp/deploy

      Note: we don't need to set the DJANGO_SETTINGS_MODULE environment
      variable for the lockserver, but it won't hurt if you do it.
      
    * In a new shell, start the lockserver:
  
        python lockserver/lockserver_daemon.py
      
      
  * Start the backend (including setting up the key database)
      
    * Create a database for the key database (e.g. called `keydb`)
  
    * Make sure that the file keydb/config.py is not readable by the user the
      website is running as (this is only something to worry about for production
      launch, if you are just developing or testing, this is not required.)

    * Edit the file keydb/config.py and set the database information for the key
      database.
    
    * Create the key database structure by executing the contents of the file
      keydb/schema.sql on the new key database you created.
      
        mysql -u[username] -p --database=[keydbname] < keydb/schema.sql

    * Edit the file backend/config.py and set a value for the authcode.
    
    * For production launch, make sure that the file backend/config.py is not
      readable by the website.

    * Set your environment variables:
  
        export PYTHONPATH=$PYTHONPATH:/tmp/deploy:/tmp/deploy/seattle
        export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'

    * In a new shell, start the backend_daemon from the backend directory
      (because the repy files need to be in the directory it is run from):
  
        cd backend
        python backend_daemon.py
      
      
  * Start the polling daemons:
  
    * Set your environment variables:
  
        export PYTHONPATH=$PYTHONPATH:/tmp/deploy:/tmp/deploy/seattle
        export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'
  
    * There's only one of these currently. To start it:
    
        python polling/check_active_db_nodes.py


  * Start the node state transition scripts:
  
    * Set your environment variables:
  
        export PYTHONPATH=$PYTHONPATH:/tmp/deploy:/tmp/deploy/seattle
        export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'
  
    * Start each transition script you intend to run:
    
        python node_state_transitions/TRANSITION_SCRIPT_NAME.py

------------------------------------------------------------------------------  

= Notes for Production =

There are two scripts provided to make updating from svn and restarting all
services easier in production. These are found in the deploymentscripts/
directory. Here is what these do:

  * update_seattlegeni_from_trunk.sh
    * This will update the trunk/ directory and redeploy seattlegeni
      to the live/ directory, backing up the old live/ directory to
      the bak/ directory.
      
  * start_seattlegeni_components.sh
    * This will start all components of seattlegeni in the correct order,
      including doing a graceful restart of apache. This script will
      remain running. You can kill this process (CTRL-C or 'kill $$')
      to stop all started components (except apache).
      
So, for example, you could keep a screen session running with
start_seattlegeni_components.sh having been run there. When it's time
to update from svn, open that screen session, do a CTRL-C, the script
will kill all of its children then exit. Once it has exited, run
update_seattlegeni_from_trunk.sh, say "y" when asked about replacing
a directory, then run start_seattlegeni_components.sh to start things
up again.

You should look at these scripts before using them on a new system, as you
might need to update paths that are used in the scripts. In general, they
assume you have a directory /home/geni and that the following directories
exist in /home/geni:

  * trunk/
    * This is the trunk directory checked out from svn.
    
  * live/
    * This is a directory that will contain the deployed seattle/ and
      seattlegeni/ directories.
      
  * bak/
    * This will contain backups of each live/ directory that is replaced
      through the use of the update_seattlegeni_from_trunk.sh script.
      
  * logs/
    * This will contain the output from each of the scripts that are part
      of seattlegeni and which get started by the
      start_seattlegeni_components.sh script.
      
It will also likely be the case that you need to start the lockserver and
backend at least once before the trying to use the website through mod_python
because the repy files will need to be translated, and the website probably
doesn't have/need permission to create files in the live/seattle/ directory.
      
If your OS distribution doesn't have django 1.1 packaged, you'll need to
install it and make sure that it is in your path (and that it is in your
path before any other installed version of django). For example, download
the django 1.1 tarball from the django website, extract it, and run the
following:

  python setup.py install --prefix=/usr/local
  
Then make sure that the following is in your path (this is for python2.5):

  /usr/local/lib/python2.5/site-packages

  
== Apache Configuration ==

Here is an example apache vhost configuration.

Lines added to an insecure http vhost:

    # Redirect requests for the server index page or that are geni-related
    # to the https site.
    RedirectMatch ^/$ https://blackbox.poly.edu/geni/html/register 
    RedirectMatch ^/geni https://blackbox.poly.edu/geni/html/register 

Lines added to a secure https vhost that users are redirected to:

    Alias /site_media "/home/geni/live/seattlegeni/website/html/media"
    <Location "/site_media">
        SetHandler None
    </Location>

    Alias /admin_media "/usr/local/lib/python2.5/site-packages/django/contrib/admin/media"
    <Location "/admin_media">
        SetHandler None
    </Location>

    <Location /geni/>
        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE seattlegeni.website.settings
        PythonOption django.root /geni
        PythonDebug Off
        # We add /usr/local/lib/python2.5/site-packages to ensure that our
        # manual installation of django 1.1 to /usr/local is in the path
        # before any copy of django installed through the distro's repositories.
        PythonPath "['/home/geni/live/', '/home/geni/live/seattle', '/usr/local/lib/python2.5/site-packages'] + sys.path"
    </Location>

    # Make sure various locations people might request redirect somewhere that works.
    RedirectMatch ^/$ https://blackbox.poly.edu/geni/html/register
    RedirectMatch ^/geni/?$ https://blackbox.poly.edu/geni/html/register
    RedirectMatch ^/geni/html/?$ https://blackbox.poly.edu/geni/html/register

    # Don't require a slash on the end of the admin url.
    RedirectMatch ^/geni/admin$ https://blackbox.poly.edu/geni/admin/
      
------------------------------------------------------------------------------

= SeattleGeni Directory Structure =

The following are the intended contents of the seattlegeni/ directory
in svn:

backend/
    
    This directory is not a package that would be imported in other code.
    This directory contains backend_daemon.py which is the single instance
    of the backend that will be running at any given time.


common/
    
    The package containing anything shared by all seattlegeni components.

  api/  
 
    This package contains a single module for each API that is used
    internally within seattlegeni. These are not intended to be used by code
    outside of seattlegeni. It may seem that, for example, the backend's API
    should live in the backend/ directory rather than here. The argument for
    why this is not the case is that the backend/ directory contains only what
    is needed to actually run the backend. The common/ directory, on the other
    hand, contains modules that may be useful to any component of seattlegeni,
    regardless of which physical system it is on.
  
  util/
  
    This package contains general utility functions.


dev/

    This directory contains modules and scripts intended for assisting testing
    during development. It will probably be removed when real testing code
    is added.


keydb/

    This is the directory where any code relevant to the keydb that is not part
    of the keydb API will go.


lockserver/
  
    This directory is not a package that would be imported in other code.
    This directory contains lockserver_daemon.py which is the single instance
    of the lockserver that will be running at any given time.
    
node_state_transitions/

    This directory contains the node state transition scripts.
    
polling/
  
    This directory is not a package that would be imported in other code.
    This directory contains the node state transition scripts, any of their
    supporting modules, and any other scripts or daemons that monitor the
    state of seattlegeni and the nodes it controls.
  
tests/

    This directory contains tests (e.g. unit tests) for seattelgeni.
    
website/

    This directory is the root of the website.
    
  control/
  
    This contains core functionality of the website regardless of the frontend
    used to access the website.
    
  html/
  
    This directory contains the code specific to the html frontend of the
    website.
    
  middleware/
  
    This is where we have defined any of our own custom django middleware.
    
  xmlrpc/
  
    This directory contains the code specific to the xmlrpc frontend of the
    website.
    

