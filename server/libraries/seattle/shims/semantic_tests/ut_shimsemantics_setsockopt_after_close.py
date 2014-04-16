#!python
"""
<Purpose>
  The purpose of this test is to test what happens when the 
  client tries to set a socket option after the socket has 
  been closed from the server side. We check to see if the
  client raises any error, or is able to set the option on 
  a closed socket.
"""

import time
import socket

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

    time.sleep(1)

    sock_server.close()
    print "[Server] Closed socket from server thread."
    # After we have accepted the connection, we do nothing.
    # This means when the client sends the data, it should
    # block eventually. We sleep so the socket object isn't
    # cleaned up.
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

# Open up a connection to the server and send a short message.
sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_client.connect((host, port))
print "[Client] Client made connection to server."

time.sleep(5)

# Attempt to set a socket option after socket has been closed.
print "[Client] Setting socket option after socket has been closed from" +\
    " a different thread"
try:
  sock_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except socket.error, err:
  print "[Client] Error raised: " + str(err)
else:
  print "[Client] No error raised."

try:
  sock_client.send("HelloWorld")
except socket.error, err:
  print "[Client] Client unable to send msg after socket closed."
else:
  print "[Client] Client still sent msg after socket was closed from server side!"

print "[Client] Setting socket option after socket has been closed from" +\
    " a different thread a second time"

try:
  sock_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except socket.error, err:
  print "[Client] Error raised second time: " + str(err)
else:
  print "[Client] No error raised second time."
