"""
<Program>
  bandwidthestimator.py

<Author>
  Brent Couvrette

<Purpose>
  Measures network capacity between computers in both directions.  Contains
  the code necesary to do both the client and server sides of these 
  measurements.
"""

def process_times(packet_times, start_index, length):
  """
  <Purpose>
    Computes the capacity estimates of the given subset of data.
  <Arguments>
    packet_times - The array of packet arrival times.
    start_index - The starting index of the longest consecutively received
                  packet train.
    length - The length of the longest consecutively received packet train.
  <Exceptions>
    None
  <Side Effects>
    Capacity results are printed.
  <Returns>
    A : delimited string of capacity results in the following form:
      max_capacity:min_capacity:median_capacity:mean_capacity
  """
  # Put all the differences into their own array
  mycontext['packet_size'] = float(mycontext['packet_size'])
  diffarray = []
  meandiff = 0
  for i in range(length-1):
    diffarray.append(packet_times[i+start_index+1] - 
                     packet_times[i+start_index])
    assert(diffarray[i] > 0)
    meandiff += diffarray[i]

  diffarray.sort()

  mindiff = diffarray[0]
  if (length-1)%2 == 0:
    mediandiff = (diffarray[(length-1)/2] + diffarray[((length-1)/2)-1])/2
  else:
    mediandiff = diffarray[(length-1)/2];

  maxdiff = diffarray[length-2]
  meandiff = meandiff/len(diffarray)
  totalmean = mycontext['packet_size']*length/(packet_times[start_index+length-1] - packet_times[start_index])
  max_cap = str(mycontext['packet_size']/mindiff)
  min_cap = str(mycontext['packet_size']/maxdiff)
  med_cap = str(mycontext['packet_size']/mediandiff)
  mean_cap = str(mycontext['packet_size']/meandiff)
  print "Results Testing from THEM to ME"
  print "Max Capacity: " + max_cap + " bytes/sec"
  print "Min Capacity: " + min_cap + " bytes/sec"
  print "Median Capacity: " + med_cap + " bytes/sec"
  print "Mean Capacity: " + mean_cap + " bytes/sec"
  return max_cap + ":" + min_cap + ":" + med_cap + ":" + mean_cap



def recv_done(remoteip, remoteport, commhandle):
  """
  <Purpose>
    When we are done receiving packets, determine the longest consecutive
    section of packets received, then compute the capacity estimates from
    that.  If we are the server, we will send our own train back to the client
    and also send the results we computed here.
  <Arguments>
    remoteip - The ip address that we should send a train and the results to
               if we are the server.
    remoteport - The port that we should send a train and the results to if we
                 are the server.
    commhandle - The commhandle that was listening for packets in the 
                 measurement train.
  <Exceptions>
    Exception raised if there isn't at least 2 consecutive packets.
  <Side Effects>
    The given commhandle is stopped.  Results are printed.  If we are the 
    server, a measurement train is sent out, as are the results from the
    train we just received.
  <Returns>
    None
  """
  # Acquire a lock to make sure only the first timer to fire does the
  # done code.
  mycontext['donelock'].acquire()
  stopcomm(commhandle)
  # Determine the longest section of packets recieved continuously and in the
  # correct order.
  if mycontext['count'][0] != -1:
    start_index = 0
    longest_length = 1
    current_length = 1
  else:
    start_index = 1
    longest_length = 0
    current_length = 0

  for i in range(1, len(mycontext['count'])):
    if mycontext['count'][i] != -1 and \
        mycontext['count'][i] > mycontext['count'][i-1]:
      current_length = current_length + 1
    else:
      if current_length > longest_length:
        longest_length = current_length
        start_index = i - longest_length

      current_length = 0

  i = i + 1
  if current_length > longest_length:
    longest_length = current_length
    start_index = i - longest_length

#  print mycontext['count']
  if longest_length < 2:
    raise Exception("Did not receive at least 2 consecutive packets.")

  # Set the first time to whatever index of count we are starting at, so we 
  # can use that as our zero time.
  results = process_times(mycontext['count'], start_index, longest_length)
  if mycontext['whoami'] == 'server':
    send_train(remoteip, remoteport, 100, 50)
    send_results(remoteip, remoteport, results)



def recv_packet(remoteip, remoteport, message, commhandle):
  """
  <Purpose>
    Receive a single packet and note the time at which it was received.
  <Arguments>
    remoteip - The ip address that the packet came from.
    remoteport - The port that the packet came from.
    message - The message that the packet contained.
    commhandle - The commhandle for the listener.
  <Exceptions>
    None
  <Side Effects>
    The timer is set/reset to 2 seconds.
  <Returns>
    None
  """
  # Note the time we received the packet.
  recvtime = getruntime()
  mycontext['donelock'].acquire()
  # Extract the packetnum from the front of the packet.
  packetnum = int(message.split('q')[0])
  mycontext['count'][packetnum] = recvtime
#  print "Received packet " + str(packetnum) + " " + str(recvtime)
  mycontext['donelock'].release()
  mycontext['timerlock'].acquire()
  # If the timer is running, cancel it, then start a new timer.
  if mycontext['timer'] is not None:
    canceltimer(mycontext['timer'])
    
  mycontext['timer'] = settimer(2, recv_done, [remoteip,remoteport,commhandle])
#  print "Reset Timer"
  mycontext['timerlock'].release()


def recv_train(ipaddr, port, packet_size, train_length):
  """
  <Purpose>
    Prepares to receive a measurement train.
  <Arguments>
    ipaddr - The local ip address that we will listen on.
    port - The local port that we will listen on.
    packet_size - The size of packets we will expect.
    train_length - The number of packets we will expect.
  <Exceptions>
    Various socket exceptions.
  <Side Effects>
    Starts listening for the measurment train packets.
  <Returns>
    None
  """
  # The count array keeps track of all the times that packets arrive.
  mycontext['count'] = [-1]*train_length
  # Set the global packet size
  mycontext['packet_size'] = packet_size
  # The timerlock makes sure that the timer is being reset by only one thread
  # at a time.
  mycontext['timerlock'] = getlock()
  # Makes sure that once the first timer fires, no other timer fires and no
  # more packets are processed.
  mycontext['donelock'] = getlock()
  mycontext['timer'] = None
  # Start listening for the packets.  We don't start the timeout timer yet
  # because we don't know when the packets will start coming.
  recvmess(ipaddr, port, recv_packet)



# Sends the given results to the given address.
def send_results(remoteip, remoteport, results):
  socket_obj = openconn(remoteip, remoteport)
  socket_obj.send(results)
  socket_obj.close()



# Sends the specified train of packets to the given destination for 
# measurement.
def send_train(ipaddr, port, packet_size, train_length):
  # We want to send train_length number of packets, all with size packet_size.
  # We also want to mark the packet with a packet number so the order can be
  # identified on the other end.
  for packetnum in range(train_length):
    sendmess(ipaddr, port, str(packetnum) + 
        "q"*(packet_size-int(packetnum/10)), getmyip(), port)


def handle_server_init(remoteip, remoteport, socket_obj, thiscommhandle, 
                       listencommhandle):
  """
  <Purpose>
    Handle a tcp connection wanting to initialize a bandwidth measurement.
  <Arguments>
    remoteip - The ip address of the computer that will be talking to us.
    remoteport - The port used by the computer that will be talking to us.
    socket_obj - The socket-like object that will be used to tell the client
                 that we are ready.
    thiscommhandle - The comm handle for this connection.
    listencommhandle - The comm handle for the listener.
  <Exceptions>
    Various socket exceptions
  <Side Effects>
    Bandwidth Measurement is started.
  <Returns>
    None
  """
  # Prepare to receive the train.
  recv_train(getmyip(), remoteport, mycontext['packet_size'], 
             mycontext['train_length'])
  # Let the other end know we are ready to receive the train.
  socket_obj.send(str(remoteip) + ":" + str(remoteport))
  socket_obj.close()
  # Now we won't do anything until we are done receiving the train (recv_done
  # is called).



def recv_results(remoteip, remoteport, socket_obj, thiscommhandle, 
                 listencommhandle):
  """
  <Purpose>
    Recieves and prints the results returned from the server.
  <Arguments>
    remoteip - The ip address of the computer that sent the results.
    remoteport - The port used by the computer to send the results.
    socket_obj - The socket-like object that will be used to receive the 
                 results.
    thiscommhandle - The comm handle for this connection.
    listencommhandle - The comm handle for the listener.
  <Exceptions>
    Various socket exceptions possible.
  <Side Effects>
    Prints the received results.  Also stops the listening comm handle.
  <Returns>
    None
  """
  # Receive the raw results, then parse them.
  rawresults = socket_obj.recv(4096)
  socket_obj.close()
  results = rawresults.split(":")
  print "Results Testing from ME to THEM"
  print "Max Capacity: " + results[0] + " bytes/sec"
  print "Min Capacity: " + results[1] + " bytes/sec"
  print "Median Capacity: " + results[2] + " bytes/sec"
  print "Mean Capacity: " + results[3] + " bytes/sec"
  stopcomm(listencommhandle)



def run_server(localip, localport, packet_size, train_length):
  """
  <Purpose>
    Runs in server mode, waiting for tcp connections to initialize measurement
    requests.
  <Arguments>
    localip - The local IP to listen on.
    localport - The local port to listen on.
  <Exceptions>
    None
  <Side Effects>
    Starts listening for connections.
  <Returns>
    None
  """
  # Note that I am the server, and thus need to send a measurement train back.
  mycontext['whoami'] = 'server'
  mycontext['packet_size'] = packet_size
  mycontext['train_length'] = train_length
  waitforconn(localip, localport, handle_server_init)



def run_client(remoteip, remoteport, localport, packet_size, train_length):
  """
  <Purpose>
    Runs in client mode, first announcing itself to a server, then sending
    measurement packets, then receiving measurement packets from the server.
  <Arguments>
    remoteip - The ip address of the remote server.
    remoteport - The port of the remote server.
    localport - The port to use locally.
  <Exceptions>
    Various socket exceptions possible.
  <Side Effects>
    Measures bandwidth both ways
  <Returns>
    None
  """
  # Note that I am the client, and thus don't need to send another measurement
  # train back when I finish receiving.
  mycontext['whoami'] = 'client'
  # Let the server know we are coming, and get back a response indicating 
  # that they are ready to do the test.
  socket_obj = openconn(remoteip, remoteport, getmyip(), localport)
  junk = socket_obj.recv(4096)
  socket_obj.close()
  mycontext['result_conn'] = waitforconn(getmyip(), localport, recv_results)
  send_train(remoteip, remoteport, packet_size, train_length)
  recv_train(getmyip(), localport, packet_size, train_length)
  
  


if callfunc == 'initialize':
  if len(callargs) != 4:
    print "Invalid arguments"
    exitall()

  if callargs[0] == 'r':
    # We are to be receiving a packet train.
    port = int(callargs[1])
    packet_size = int(callargs[2])
    train_length = int(callargs[3])
    run_server(getmyip(), port, packet_size, train_length)
  else:
    # We are to be sending a packet train.
    ipaddr = callargs[0]
    port = int(callargs[1])
    packet_size = int(callargs[2])
    train_length = int(callargs[3])
    run_client(ipaddr, port, port, packet_size, train_length)
