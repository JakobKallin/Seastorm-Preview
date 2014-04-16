#!python
"""
<Purpose>
  The purpose of this test is to test what the default behavior
  of bind is when we don't specify the host.
"""

import time
import socket

from threading import Thread


host = '127.0.0.1'

# This portion is used to find a suitable port.
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, 0))
try:
    sock.connect(("gmail.com", 80))
except socket.error, err:
    print "[Client] Attempting to connect to external address while binding socket to loopback address."
    print "[Client] Received error '%s'" % str(err)
sock.close()
del sock
