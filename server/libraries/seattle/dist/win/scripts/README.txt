Seattle: the Internet as a Testbed

Seattle is a platform for networking and distributed systems research.  It's
free, community-driven, and offers a large deployment of computers spread across
the world.  Seattle runs on end user systems on diverse platforms in a safe and
contained manner.  This is achieved primarily by the use of repy (Restricted
Python, a subset of Python) which appropriately restricts the kinds of advanced
operations that could compromise the machines running our software.  To learn
in more detail about Seattle and how it works, visit our wiki:
https://seattle.cs.washington.edu




Installation Instructions:
install.bat

Simply click the install.bat icon to install Seattle on your system. The
installation process involves configuring our files to work correctly on your
system, generating the encryption keys to be used by our Node Manager program,
and setting up Seattle to run in the background in order to manage the resources
you are donating to the project.

FOR ADVANCED USERS:
If you plan to install Seattle from the command line, below are options that can
be passed to the installer:

install.bat [--nm-key-bitsize bitsize]
--nm-key-bitsize bitsize: specify the bitsize of the encryption keys that the
		          Node Manager will use. Default: 1024 bits.




Uninstall Instructions:
uninstall.bat

To uninstall, which will cause Seattle to stop running on your system and
prevent you from donating resources from your machine, click the uninstall.bat
icon.  After doing this, it is safe to completely remove the Seattle directory
from your system.




Useful Commands:
stop_seattle.bat

To temporarily stop Seattle from running on your machine, click the
stop_seattle.bat icon.  This will disable Seattle from running either until
you click the start_seattle.bat icon or reboot your machine, whichever occurs
first.


start_seattle.bat
To restart Seattle running on your system, simply click the start_seattle.bat
icon.  After doing this, Seattle will run as though it had never been stopped
after the installation.

seash.py
If you are a developer as well as a user, you can use the copy of the 
Seattle shell which is included in your installer.   Simply run
python seash.py to access the shell.   See the wiki for more information
about using the shell.

repy.py
Developers can also run programs locally using a local instance of repy.
This allows you to experiment with your programs locally before deploying
them on remote machines.



Contact Us:
For much more information on this project, visit our wiki:
https://seattle.cs.washington.edu

For support, post a message to all the developer email list serve:
seattle-users@cs.washington.edu

To subscribe to our email list serve, used by our developers, follow this link:
https://mailman.cs.washington.edu/mailman/listinfo/seattle-users
