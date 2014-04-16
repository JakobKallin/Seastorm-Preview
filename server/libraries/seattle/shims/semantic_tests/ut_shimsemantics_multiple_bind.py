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
sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock1.bind((host, port))

# Try to bind the second socket to the same host:port.
# This should fail as sock1 has already binded to it.
sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock2.bind((host, port))
