To run the backend do the following:

  * Create a new directory, we'll call it /path/to/deploy
  * Create a directory called seattle in the deploy directory, that is, /path/to/deploy/seattle
  * cp nodemanager/* portability/* repy/* seattlelib/* /path/to/deploy/seattle/
  * touch /path/to/deploy/__init__.py
  * export PYTHONPATH=$PYTHONPATH:/path/to/deploy:/path/to/deploy/seattle

Note that both /path/to/deploy and /path/to/deploy/seattle need to be in the
path. This is because seattlegeni will be looking for a package named 'seattle'
which contains all of the repy and other modules, and existing code in those
modules will be importing without any package names.

E.g. seattlegeni uses:

from seattle import X

and the rest of the codebase currently uses:

import X


