# Warning: settings must be imported and the database values modified before
# anything else is imported. Failure to do this first will result in django
# trying to create a test mysql database.
from seattlegeni.website import settings

import os
import sys
import tempfile

# Use a database file that actually resides in memory, if possible.
# Note that we do this instead of use TEST_DATABASE_NAME = ":memory:" because
# there seems to be a problem with additional threads accessing the test
# database in memory when using an in-memory sqlite database (":memory:")
# rather than a file-backed one.
# The use of Python 2.5 with /dev/shm as the location of the sqlite db may also
# may be the cause of some tests failing on testbed-opensuse due to locks not
# being released, most likely, so we'll only use /dev/shm for 2.6+.
if os.path.exists("/dev/shm") and sys.version_info >= (2, 6):
  sqlite_database_file_dir = "/dev/shm"
else:
  sqlite_database_file_dir = None

# Do not change the DATABASE_ENGINE. We want to be sure that sqlite3 is used
# for tests.
settings.DATABASE_ENGINE = 'sqlite3'

# We just want the name of a temporary file that we'll use multiple times.
# We don't want it to exist already, so we remove it after creating it. This is
# not for anything security sensitive, it will only be used for test sqlite
# databases. We could just make up a random name of our, really.
test_db_filehandle, test_db_filename = tempfile.mkstemp(dir=sqlite_database_file_dir, suffix=".sqlite")
os.close(test_db_filehandle)
os.remove(test_db_filename)

settings.TEST_DATABASE_NAME = test_db_filename
# We set the DATABASE_OPTIONS for two reasons:
#   1. We need to get rid of the init_command that we have for mysql in our
#      default settings.py
#   2. We need to have a high enough timeout for sqlite to obtain a lock.
#      The default is normally 5 seconds but was 0 seconds in some earlier
#      versions of pysqlite. I was getting the 'database is locked' error
#      on testbed-opensuse and found the suggestion of increasing this value
#      here: http://code.djangoproject.com/ticket/9409
#      However, this still doesn't seem to completely solve the issue. It may
#      be an issue with python 2.5's sqlite.
settings.DATABASE_OPTIONS = {'timeout':30}

# Remove the CSRF middleware as our tests don't try to send csrf tokens. We're
# not the only ones who ignore this for testing:
# http://code.djangoproject.com/ticket/11692
new_middleware_classes = list(settings.MIDDLEWARE_CLASSES)
new_middleware_classes.remove('django.contrib.csrf.middleware.CsrfViewMiddleware')
new_middleware_classes.remove('django.contrib.csrf.middleware.CsrfResponseMiddleware')
settings.MIDDLEWARE_CLASSES = tuple(new_middleware_classes)

import django.db

import django.test.utils

from seattlegeni.common.util import log





# Turn off most logging to speed up tests run manually. This can be removed
# to see the plentiful debug output.
log.set_log_level(log.LOG_LEVEL_CRITICAL)





def setup_test_environment():
  """
  Called once before running one or more tests. Must be called before calling
  setup_test_db().
  """
  
  django.test.utils.setup_test_environment()



def teardown_test_environment():
  """
  Called once after running one or more tests. That is, this should be called
  before the test script exits.
  """
  
  django.test.utils.teardown_test_environment()



def setup_test_db():
  
  # Creates a new test database and runs syncdb against it.
  django.db.connection.creation.create_test_db()





def teardown_test_db():
  
  # We aren't going to use any database again in this script, so we give django
  # an empty database name to restore as the value of settings.DATABASE_NAME.
  old_database_name = ''
  django.db.connection.creation.destroy_test_db(old_database_name)
  
