import sys
import time

dy_import_module_symbols("shimstackinterface")

SERVER_IP = getmyip()
SERVER_PORT = 34829
DATA_TO_SEND = "HelloWorld" * 1024 * 1024

RECV_SIZE = 2**10 # 16384 bytes.

END_TAG = "@@END"

SLEEP_TIME = 0.01

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

  # The two ShimStackInferface objects for comparing one shim string to the
  # default shim string.
  shim_commpr_object = ShimStackInterface(SHIM_STRING_SERVER)
  shim_noop_object = ShimStackInterface(SHIM_STRING_SERVER_DEFAULT)

  tcpserver_commpr_socket = shim_commpr_object.listenforconnection(SERVER_IP, SERVER_PORT)
  tcpserver_noop_socket = shim_noop_object.listenforconnection(SERVER_IP, SERVER_PORT + 1)

  while True:
    try:
      rip, rport, sockobj = tcpserver_commpr_socket.getconnection()
      break
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break

  msg_received = ''

  # Echo back all the message that we receive. Exit out of the 
  # loop once we get socket closed error.
  while True:
    try:
      rcv = sockobj.recv(RECV_SIZE)
      msg_received += rcv
     
      if END_TAG in rcv:
        break
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break
    

  while msg_received:
    try:
      data_sent = sockobj.send(msg_received)
      msg_received = msg_received[data_sent : ]
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break


  # Now we will try to listen and echo back on a NoopShim
  while True:
    try:
      rip, rport, noop_sockobj = tcpserver_noop_socket.getconnection()

      break
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break


  msg_received = ''

  # Echo back all the message that we receive on a noop shim. Exit out of the
  # loop once we get socket closed error or if the END_TAG is received
  while True:
    try:
      rcv = noop_sockobj.recv(RECV_SIZE)
      msg_received += rcv

      if END_TAG in rcv:
        break
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break


  while msg_received:
    try:
      data_sent = noop_sockobj.send(msg_received)
      msg_received = msg_received[data_sent : ]
    except SocketWouldBlockError:
      sleep(SLEEP_TIME)
    except (SocketClosedLocal, SocketClosedRemote):
      break






def launch_test():

  # Launch the server and sleep for couple of seconds.
  createthread(launchserver)
  sleep(3)

  shim_obj = ShimStackInterface(SHIM_STRING_CLIENT)

  try:
    sockobj = shim_obj.openconnection(SERVER_IP, SERVER_PORT, SERVER_IP, SERVER_PORT + 2, 10)
  except Exception, err:
    print "Found error while openconning CompressionShim: " + str(err)
    exitall()




# ---------------------------- Testing Compression Upload -------------------------
  msg_to_send = DATA_TO_SEND + END_TAG

  cur_data_sent = 0
  log("\nStarting to send data through Compression Shim.............\n")
  start_time = getruntime()

  while msg_to_send:
    try:
      data_sent = sockobj.send(msg_to_send)
    except SocketWouldBlockError, err:
      sleep(SLEEP_TIME)
    else:
      msg_to_send = msg_to_send[data_sent:]
      cur_data_sent += data_sent

  send_end_time = getruntime()
  send_rate = cur_data_sent / (send_end_time - start_time) / 1024
                        
  log("Time to send %d bytes of data through Compression: %.4fs (%.2f Kb/s)" % (cur_data_sent, send_end_time - start_time, send_rate))

# -------------------------- Testing Compression Download ------------------------------
  msg_received = ''
  cur_data_recv_buf = ''

  log("\nStarting to recv echo msg from Compression Shim.")
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

  recv_end_time = getruntime()
  sockobj.close()
  recv_rate = len(msg_received) / (recv_end_time - send_end_time) / 1024

  log("\nTime taken to receive echo msg through Compression (%d bytes): %.4fs (%.4f Kb/s)" % (len(msg_received), (recv_end_time - send_end_time), recv_rate))


  sleep(3)
# ----------------------- Testing Noop Upload -------------------------------

  try:
    noop_sockobj = shim_obj.openconnection(SERVER_IP, SERVER_PORT + 1, SERVER_IP, SERVER_PORT + 3, 10)
  except Exception, err:
    print "Found error while openconning NoopShim: " + str(err)
    exitall()


  msg_to_send = DATA_TO_SEND + END_TAG

  cur_data_sent = 0
  log("\n\nStarting to send data through Noop Shim.............\n")

  noop_start_time = getruntime()

  while msg_to_send:
    try:
      data_sent = noop_sockobj.send(msg_to_send)
    except SocketWouldBlockError, err:
      sleep(SLEEP_TIME)
    else:
      msg_to_send = msg_to_send[data_sent:]
      cur_data_sent += data_sent

  noop_send_end_time = getruntime()
  noop_send_rate = cur_data_sent / (noop_send_end_time - noop_start_time) / 1024

  log("Time to send %d bytes of data through Noop: %.4fs (%.2f Kb/s)" % (cur_data_sent, noop_send_end_time - noop_start_time, noop_send_rate))


# --------------------- Testing Noop Download ---------------------------------

  msg_received = ''
  cur_data_recv_buf = ''

  log("\nStarting to recv echo msg from Noop Shim.")
  while True:
    try:
      data_received = noop_sockobj.recv(RECV_SIZE)
    except SocketWouldBlockError, err:
      sleep(SLEEP_TIME)
    else:
      msg_received += data_received
      cur_data_recv_buf += data_received
      if END_TAG in data_received:
        break

  noop_recv_end_time = getruntime()
  noop_sockobj.close()
  noop_recv_rate = len(msg_received) / (noop_recv_end_time - noop_send_end_time) / 1024

  log("\nTime taken to receive echo msg through Noop (%d bytes): %.4fs (%.4f Kb/s)" % (len(msg_received), (noop_recv_end_time - noop_send_end_time), noop_recv_rate))



# -------------------------- Assert Check some things ----------------------------  

  log("\n\nChecking message received len: ")
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
    log("[ FAIL ]")
    exitall()
  else:
    log("[ PASS ]")
 
  log("\nChecking if CompressionShim upload rate > NoopShim upload rate: ")
  try:
    assert(send_rate > noop_send_rate)
  except AssertionError:
    log("[ FAIL ]")
  else:
    log("[ PASS ]")

  log("\nChecking if CompressionShim download rate > NoopShim download rate: ")
  try:
    assert(recv_rate > noop_recv_rate)
  except AssertionError:
    log("[ FAIL ]")
  else:
    log("[ PASS ]")

  log("\n\nTotal time taken: %.4fs\n\n" % (noop_recv_end_time - start_time))

  log("\n\nNOTE:\tThe last two test cases may fail in some instances (small\n"
      "\tdata transfer, random data transfer etc.) Please use your\n"
      "\tjudgement for those two cases.\n")

  exitall()

