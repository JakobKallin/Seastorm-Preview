"""
<Program Name> 
  BandwidthClient.py

<Started>
  Feb 2 2009

<Authors> 
  Anthony Honsta 
  Carter Butaud
  
"""

def get_mess(size, idstring, index):
  mess = idstring + "|" + str(index) + "|"
  return mess + "0" * (size - len(mess))
  
def do_nothing(ip, port, mess, ch):
  pass
  
def get_bandwidth(server_ip):
  ip = getmyip()
  mycontext["tcp_port"] = 12345
  mycontext["udp_port"] = 12346
  mycontext["server_ip"] = server_ip

  num_to_send = 30 # number of packets to be sent
  
  # Open a tcp connection to the server
  server_conn = openconn(mycontext["server_ip"], mycontext["tcp_port"])
  server_conn.send(str(num_to_send))
  server_conn.close()
    
  # Listening on the channel we plan to send on increases the send speed
  connhandle = recvmess(ip, mycontext["udp_port"], do_nothing)

  # Send the UDP packet train
  for i in range(num_to_send):
    mess = get_mess(512, "testing", i)
    sendmess(mycontext["server_ip"], mycontext["udp_port"], mess, ip, mycontext["udp_port"])
 
  sleep(1)
  
  # Open the final tcp connection with the server to
  # transmit closing string and recieve test results.
  server_conn = openconn(mycontext["server_ip"], mycontext["tcp_port"])
  server_conn.send("Done.")
  
  data = server_conn.recv(200)
  server_conn.close()
  
  stopcomm(connhandle)
  return int(float(data))
    
if callfunc == "initialize":
  if len(callargs) < 1:
    print "Invalid usage: a server ip is required."
  else:
    print get_bandwidth(callargs[0])

 
