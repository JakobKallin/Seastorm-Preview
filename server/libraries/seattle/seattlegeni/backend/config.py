"""
This file must be readable by the backend and should only be readable by client
code that is allowed to make privileged requests to the backend. Basically,
it should *not* be readable by the user the webserver/website runs as.

The reason for the restrictions is explained in backend_daemon.py, but
basically it's that we want the backend to be the place where all node-
"""

# Change this for production usage.
authcode = "FILL_THIS_IN"
