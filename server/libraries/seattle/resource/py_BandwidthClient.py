"""
<Program Name> 
  BandwidthClient.py

<Started>
  Feb 2 2009

<Authors> 
  Anthony Honsta 
  Carter Butaud
  
"""
import sys
callargs = []
if len(sys.argv) > 1:
  callargs = sys.argv[1:]
from repyportability import *
mycontext = {}

def get_mess(size, idstring, index):
  mess = idstring + "|" + str(index) + "|"
  return mess + "0" * (size - len(mess))
  
def do_nothing(ip, port, mess, ch):
  pass
  
def get_bandwidth(server_ip, server_port, packet_size, packet_count):
  local_ip = getmyip()
  local_port = 12345

  num_to_send = packet_size # number of packets to be sent
  
  # Open a tcp connection to the server
  server_conn = openconn(server_ip, server_port)
  server_conn.send(str(num_to_send))
  server_conn.close()
    
  # Listening on the channel we plan to send on increases the send speed
  connhandle = recvmess(local_ip, local_port, do_nothing)

  # Send the UDP packet train
  for i in range(num_to_send):
    mess = get_mess(packet_size, "testing", i)
    sendmess(server_ip, server_port, mess, local_ip, local_port)
 
  sleep(1)
  
  # Open the final tcp connection with the server to
  # transmit closing string and recieve test results.
  server_conn = openconn(server_ip, server_port)
  server_conn.send("Done.")
  
  data = server_conn.recv(200)
  server_conn.close()
  stopcomm(connhandle)
  return int(float(data))
    
if __name__ == "__main__":
  if len(callargs) < 1:
    print "Invalid usage: a server ip is required."
  else:
    print get_bandwidth(callargs[0], 12345, 512, 300)

 
