#!python
"""
<Purpose>
  This test is to show multicast failing on different
  OSes. This test case was taken straight from:
  http://bugs.python.org/issue1462440
  http://bugs.python.org/file1939/multicastbug.py

"""

# demonstrates multicast udp
from threading import *
from socket import *
import time
ifaddr = '127.0.0.1'
mcaddr = '224.0.0.1'
port = 40000

def rcv():
    s = socket(AF_INET, SOCK_DGRAM)
    sopt = inet_aton(mcaddr) + inet_aton(ifaddr)
    s.setsockopt(SOL_IP, IP_ADD_MEMBERSHIP, sopt)
    s.settimeout(5)
    s.bind(("", port))
    for i in range(3):
        try:
            msg = s.recvfrom(1024)
        except socket.error, err:
            print '[Server] Error raised: ' + str(err)
        else:
            print '[Server] Received message: ' + str(msg)

def snd():
    s = socket(AF_INET, SOCK_DGRAM)
    s.settimeout(5)
    for i in range(3):
        print "[Client] Sending message."
        s.sendto("HelloWorld!", (mcaddr, port))
        time.sleep(1)

t1 = Thread(target=rcv, name='rcv')
t2 = Thread(target=snd, name='snd')

t1.start()
t2.start()
