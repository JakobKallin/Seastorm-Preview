#!python
"""
<Purpose>
  The purpose of this test is to see what happens if the 
  client sends a large datagram, and the server tries to receive
  a datagram size that is half of the sending size.
"""

import time
import socket

import threading

host = '127.0.0.1'

# This is the server thread that will wait for a connection.
class server(threading.Thread):
  def __init__(self, host, port, sock_server):
    threading.Thread.__init__(self)
    self.host = host
    self.port = port
    self.sock_server = sock_server
    self._stop = threading.Event()

  def run(self):
    self.sock_server.bind((self.host, self.port))
    self.sock_server.settimeout(5)

    print "[Server] Started UDP server and ready to receive a datagram of size 1024."
    # This should block and not raise any error. The socket
    # will be closed from the main thread while its blocking
    # on recv.
    i = 0
    while True:
      try:
        (data, addr) = self.sock_server.recvfrom(1024)
        print "[Server][MSG:%d] Received data of size %d " % (i, len(data))
      except Exception, err:
        if 'timed out' in str(err):
          break
        print "[Server] Received exception on recv: '%s'" % str(err)

      i+=1

      


  def stop(self):
    self._stop.set()



# This portion is used to find a suitable port.
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((host, 0))
port = sock.getsockname()[1]
sock.close()
del sock



sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Start the server then wait couple of seconds 
# before closing the socket that is blocking on recvfrom.
server_thread = server(host, port, sock_server)
server_thread.start()


# Send an UDP datagram to the server.
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Wait for the server to start up.
time.sleep(1)

# Send a message that is twice the size that the server is receiving.
message_dgram = "Ahoy" * 8 

for i in range(10):
  data_sent = client_sock.sendto(message_dgram, (host, port))
  print "[Client][MSG:%d] Sent a datagram to the server of size %d." % (i,data_sent)
  message_dgram = message_dgram * 2

time.sleep(2)

# Close the socket server that is blocking on recv.
sock_server.close()





