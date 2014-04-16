#!python
"""
<Purpose>
  The purpose of this test is to test what happens when the a socket
  that is blocking on recv is closed in another thread.
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
    
    # This should block and not raise any error. The socket
    # will be closed from the main thread while its blocking
    # on recv.
    try:
      (data, addr) = self.sock_server.recvfrom(1024)
      print "[Server] Received data: " + data
    except Exception, err:
      if str(err) == 'timed out':
        print "[Server] Received exception on recv: '%s'" % str(err)
        print "[Server] Test failed. Got timeout error due to timeout being set."
        print "\tExpecting socket closed error."

      else:
        print "[Server] Received exception on recv: '%s'" % str(err)
        print "\tMight be the right error. Need human judgement."

  def stop(self):
    self._stop.set()



# This portion is used to find a suitable port.
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((host, 0))
port = sock.getsockname()[1]
sock.close()
del sock



sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_server.settimeout(5)

# Start the server then wait couple of seconds 
# before closing the socket that is blocking on recvfrom.
server_thread = server(host, port, sock_server)
server_thread.start()

time.sleep(3)

# Close the socket server that is blocking on recv.
sock_server.close()
print "[Client] Closed socket that is blocking on recv. Should raise a socket closed/unreachable error next by server."




