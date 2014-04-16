#!python
"""
<Purpose>
  The purpose of this test is to test what the default behavior
  of inheritance of flags is in python. That is, without setting
  the O_NONBLOCK flag, what is the behavior on different systems.
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
    #sock_server.settimeout(None)
    sock_server.setblocking(0)
    sock_server.listen(1)
    
    while True:
      try:
        conn, addr = sock_server.accept()
        break
      except:
        time.sleep(0.1)

    # This should block and not raise any error.
    try:
      data = conn.recv(1024)
      print "[Server] Received data: " + data
      print "[Server] Was expecting a socket blocking error. Test failed."
    except Exception, err:
      print "[Server] Received exception on recv. %s" % str(err)
      print "[Server] Test passed"



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

time.sleep(5)
sock_client.send('Hello World')
print "[Client] Sent data after sleeping"
sock_client.close()





