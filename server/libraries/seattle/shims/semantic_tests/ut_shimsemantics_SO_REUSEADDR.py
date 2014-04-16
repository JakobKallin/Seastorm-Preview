import socket

# This portion is used to find a suitable port.
host = '127.0.0.1'
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, 0))
port = sock.getsockname()[1]
sock.close()
del sock

# Bind the first socket to an host:port.
sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock1.bind((host, port))

print "[CLient] Binding socket 1 to (%s:%d)" %  (host, port) 
print "[Client] Attempting to bind a second socket to the same host:port"

# Try to bind the second socket to the same host:port.
# This should fail as sock1 has already binded to it.
sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    sock2.bind((host, port))
except socket.error, err:
    print "[Client] Unable to bind the second socket to the same address while using SO_REUSEADDR. '%s'" % str(err)
else:
    print "[CLient] Managed to bind the second socket to the same host:port while using SO_REUSEADDR"
