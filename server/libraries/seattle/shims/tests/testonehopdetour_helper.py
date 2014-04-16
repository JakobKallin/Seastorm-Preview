import sys
import time

dy_import_module_symbols("shimstackinterface")

SERVER_IP = getmyip()
SERVER_PORT = 34825
UPLOAD_LIMIT = 1024 * 1024 * 128 # 128MB
DOWNLOAD_LIMIT = 1024 * 1024 * 128 # 128MB
TIME_LIMIT = 60
DATA_TO_SEND = "HelloWorld" * 5

RECV_SIZE = 2**14 # 16384 bytes.
MSG_RECEIVED = ''
END_TAG = "@@END"

FINISHED_SENDING = False

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

  shim_object = ShimStackInterface("(CoordinationShim)(OneHopDetourShim)")

  udpserver_socket = shim_object.listenformessage(SERVER_IP, SERVER_PORT)

  total_received = ''

  # Keep trying to receive UDP datagrams while all messages haven't been sent yet.
  while not FINISHED_SENDING:
    try:
      rip, rport, msg_received = udpserver_socket.getmessage()
      total_received += msg_received
    except SocketWouldBlockError:
      sleep(0.01)
    except SocketClosedLocal:
      print "Shouldn't have been here"
      break
    except Exception, err:
      print str(err)
      break
    


  try:
    assert(total_received == DATA_TO_SEND)
  except AssertionError:
    print "Message received did not match. Received: " + total_received
  else:
    print "Message received checks out! Received: " + total_received




def launch_test():

  # Launch the server and sleep for couple of seconds.
  createthread(launchserver)
  sleep(3)

  global FINISHED_SENDING

  shim_obj = ShimStackInterface("(CoordinationShim)")

  data_left = DATA_TO_SEND

  while data_left:
    try:
      byte_sent = shim_obj.sendmessage(SERVER_IP, SERVER_PORT, data_left, SERVER_IP, SERVER_PORT + 1)
      data_left = data_left[byte_sent:]
    except Exception, err:
      print "Found error: " + str(err)
      raise


  sleep(5)
  FINISHED_SENDING = True
  sleep(3)
  print "Finished test."
  exitall()
