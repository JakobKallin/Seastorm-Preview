#!python
"""
<Purpose>
  The purpose of this test is to test what happens when the 
  client sends data multiple times without having the server
  receiver receive any data. The big buffer at the OS level
  should buffer all the data. According to:
  http://twistedmatrix.com/pipermail/twisted-python/2004-August/008461.html
  apparently Windows does not append new data to the buffer, instead
  it waits for the buffer to be completely empty.
"""

import sys
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
sock_client.setblocking(0)

time.sleep(1)

# We first keep sending data until we receive the buffer full 
# error, then we sleep for a bit then try to send a data again.
while True:
  try:
    data_sent = sock_client.send('HelloWorld'*1024*1024)
  except socket.error, err:
    print "[Client] Send has filled up the OS buffer. '%s' " % str(err)
    break

# Sleep for a while before sending.
time.sleep(3)    

try:
  data_sent2 = sock_client.send('HelloWorld'*1024*512)
except Exception, err:
  print "[Client] Got error on second send. Unable to add data to OS buffer until buffer is completely empty."
else:
  print "[Client] Successfully added data to an almost full buffer without waiting for buffer to be completely empty.."
    
sock_client.close()
sys.exit(1)




