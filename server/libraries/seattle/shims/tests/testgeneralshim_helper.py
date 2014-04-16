import sys
import time

dy_import_module_symbols("shimstackinterface")

SERVER_IP = getmyip()
SERVER_PORT = 34829

CLIENT_IP = getmyip()
CLIENT_PORT = 35247

DATA_TO_SEND = "HelloWorld" * 1024 * 1024

RECV_SIZE = 2**10 # 16384 bytes.

END_TAG = "@@END"

SLEEP_TIME = 0.01

SERVER_SHIM_STRING = "(CoordinationShim)(NoopShim)"
CLIENT_SHIM_STRING = "(CoordinationShim)"

def launchserver():
  """
  <Purpose>
    Launch a server that receives and echos the message back.

  <Arguments>
    None

  <Side Effects>
    None

  <Exceptions>
    None

  <Return>
    None
  """

  shim_object = ShimStackInterface(SERVER_SHIM_STRING)

  tcpserver_socket = shim_object.listenforconnection(SERVER_IP, SERVER_PORT)

  while True:
    try:
      rip, rport, sockobj = tcpserver_socket.getconnection()
      break
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break

  msg_received = ''
  recv_closed = False
  send_closed = False

  # Echo back all the message that we receive. Exit out of the 
  # loop once we get socket closed error.
  while True:
    try:
      rcv = sockobj.recv(RECV_SIZE)
      msg_received += rcv
     
      if END_TAG in rcv:
        break
    except SocketWouldBlockError:
      pass
    except (SocketClosedLocal, SocketClosedRemote):
      break
    

  while msg_received:
    try:
      data_sent = sockobj.send(msg_received)
      msg_received = msg_received[data_sent : ]
    except SocketWouldBlockError:
      pass
    except (SocketClosedLocal, SocketClosedRemote):
      break






def launch_test():

  # Launch the server and sleep for couple of seconds.
  createthread(launchserver)
  sleep(3)

  shim_obj = ShimStackInterface(CLIENT_SHIM_STRING)

  try:
    sockobj = shim_obj.openconnection(SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT, 10)
  except Exception, err:
    print "Found error: " + str(err)
    exitall()

  print "Made the connection to server!"

  msg_to_send = DATA_TO_SEND + END_TAG



  cur_data_sent = 0
  while msg_to_send:
    try:
      data_sent = sockobj.send(msg_to_send)
    except SocketWouldBlockError, err:
      sleep(SLEEP_TIME)
    else:
      msg_to_send = msg_to_send[data_sent:]
      cur_data_sent += data_sent

  print "Sent the entire message"

# -------------------------- Testing Download ------------------------------
  msg_received = ''
  cur_data_recv_buf = ''

  log("\nStarting to recv echo msg.")
  while True:
    try:
      data_received = sockobj.recv(RECV_SIZE)
    except SocketWouldBlockError, err:
      sleep(SLEEP_TIME)
    else:
      msg_received += data_received
      cur_data_recv_buf += data_received
      if END_TAG in data_received:
        break
  else:
    log("[ PASS ]")

  sockobj.close()


  log("\nChecking message received len: ")
  try:
    assert(len(msg_received) == len(DATA_TO_SEND + END_TAG))
  except AssertionError:
    log("[ FAIL ]")
    exitall()
  else:
    log("[ PASS ]")
    
  log("\nChecking if sent message matches echo message: ")
  try:
    assert(msg_received == DATA_TO_SEND + END_TAG)
  except AssertionError:
    log("[ FAIL ]\n")
    exitall()
  else:
    log("[ PASS ]\n")

  exitall()
