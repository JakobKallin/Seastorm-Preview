#!python
"""
<Purpose>
  The purpose of this test is to test what happens when we try
  to broadcast a message without using the broadcast flag.
"""

import sys
import time
import socket

from threading import Thread

#host = '127.0.0.1'
host = ''

# This is the server thread that will wait for a connection.
class server(Thread):
  def __init__(self, host, port):
    Thread.__init__(self)
    self.host = host
    self.port = port

  def run(self):
    sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_server.settimeout(5)
    sock_server.bind((self.host, self.port))

    # Receive a broadcast message.
    try:
      message, address = sock_server.recvfrom(1024)
    except socket.error:
      print "[Server] Server did not receive broadcast message."
    else:
      print "[Server] Server received message from %s" % str(address) 




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

# Open up a connection to the server and send a short message.
sock_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

time.sleep(1)

# We send a broadcast message without having set the SO_BROADCAST
# flag. This should still work.
try:
  data_sent = sock_client.sendto('HelloWorld', ('<broadcast>', port))
except socket.error:
  print "[Client] Unable to send broadcast message without setting the SO_BROADCAST flag."
else:
  print "[Client] Sent broadcast message without setting the SO_BROADCAST FLAG."

sock_client.close()




