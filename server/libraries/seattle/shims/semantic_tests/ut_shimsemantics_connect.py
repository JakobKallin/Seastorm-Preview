import socket

sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock.settimeout(15.0)

# Try to connect to a random port that no one is listening on.
try:
    result = sock.connect(('127.0.0.1', 34567))  
except socket.error, err:
    print "[Client] Attempting to connect to an unavailable host:port."
    print "[Client] Received error '%s'" % str(err)
