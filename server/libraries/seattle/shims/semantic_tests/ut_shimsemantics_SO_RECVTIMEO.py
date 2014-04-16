#!python
"""
This test is to see how the setsockopt for SO_RCVTIMEO behaves
across different platforms.
"""

import time
import socket
import struct

from threading import Thread

host = '127.0.0.1'

# This is the server thread that will wait for a connection.
class server(Thread):
  def __init__(self, host, port):
    Thread.__init__(self)
    self.host = host
    self.port = port

  def run(self):
    sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_server.bind((self.host, self.port))
    sock_server.listen(1)
    
    while True:
      try:
        conn, addr = sock_server.accept()
        break
      except:
        time.sleep(0.1)

    # Do nothing after connecting to socket.
    time.sleep(5)




# This portion is used to find a suitable port.
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, 0))
port = sock.getsockname()[1]
sock.close()
del sock



# Start the server then wait couple of seconds 
# before sending it message.
server_thread = server(host, port)
server_thread.start()
time.sleep(1)



sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

opt = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 30)
print "[CLient] Existing timeout is '%s'" % str(struct.unpack('LL', opt))

print "[CLient] Will now set timeout to 3 secs, 34567 microsecs..."
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 3, 34567))

opt = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 30)
print "[Client] Timeout is now '%s'" % str(struct.unpack('LL', opt))

print "[Client] Will now set timeout to it's existing value (ie. expect no change)..."
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, opt)

opt = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 30)
print "[Client] Timeout is now '%s'" % str(struct.unpack('LL', opt))

sock.connect((host, port))

print "[Client] Attempting to receive."

start_time = time.time()
try:
    sock.recv(1024)
except:
  pass

print "[Client] Time to return from recv: '%f'. Should be around 3.034567 seconds." % (time.time() - start_time)

