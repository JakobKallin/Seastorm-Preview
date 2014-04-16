import sys
import os
import time
import unittest
import subprocess

from os.path import join

# In the tests below, the known nodes are 127.0.0.1:12345 and 127.0.0.1:12346.
# 127.0.0.1:20000 is used as an unknown node for tests that require it. At least
# on Windows, some of these tests often fail due to CleanupInProgressError.
# Ticket #1067 suggests that this is also the case on Mac
# (https://seattle.poly.edu/ticket/1067).
expectations = {
  'udp_send': {
    'sender': 'send,1,127.0.0.1:12346,*\n'
  },
  'udp_send_receive': {
    'sender': 'send,1,127.0.0.1:12346,*\n',
    'recipient': 'receive,2,1,127.0.0.1:12345,*\n'
  },
  'tcp_send': {
    'sender': ''
  },
  'tcp_send_receive': {
    'sender': 'send,1,127.0.0.1:12346,hello\n',
    'recipient': 'receive,2,1,127.0.0.1:12345,hello\n'
  },
  # In this test, both the sender and the recipient start sending before
  # receiving anything.
  'tcp_send_receive_duplex_simultaneous': {
    'sender':
      'send,1,127.0.0.1:12346,sender-payload\n' +
      'receive,2,1,127.0.0.1:12346,recipient-payload\n',
    'recipient':
      'send,1,127.0.0.1:12345,recipient-payload\n' +
      'receive,2,1,127.0.0.1:12345,sender-payload\n'
  },
  # In this test, the recipient starts sending only after receiving something
  # from the sender.
  'tcp_send_receive_duplex_sequential': {
    'sender':
      'send,1,127.0.0.1:12346,sender-payload\n' +
      'receive,3,2,127.0.0.1:12346,recipient-payload\n',
    'recipient':
      'send,2,127.0.0.1:12345,recipient-payload\n' +
      'receive,3,1,127.0.0.1:12345,sender-payload\n'
  },
  'tcp_send_partial_timestamp': {
    'recipient': 'receive,1235,1234,127.0.0.1:12345,hello\n'
  },
  'tcp_send_only_timestamp': {
    'recipient': 'receive,1235,1234,127.0.0.1:12345,hello\n'
  },
  'udp_unknown_sender': {
    'recipient': ''
  },
  'tcp_unknown_sender': {
    'recipient': ''
  },
  'udp_unknown_recipient': {
    'sender': ''
  },
  'tcp_unknown_recipient': {
    'sender': ''
  },
  # The tests below check that log entries are properly added even when the user
  # forgets to call `close()`. This is currently done by using Python's
  # `__del__` method, but this does not seem to run in programs with a single
  # context. For that reason, these tests run everything inside a function. The
  # problem has not yet been solved for single-context programs.
  'sender_socket_unclosed': {
    'sender': 'send,1,127.0.0.1:12346,hello\n'
  },
  'recipient_socket_unclosed': {
    'recipient': 'receive,2,1,127.0.0.1:12345,hello\n'
  },
  'both_sockets_unclosed': {
    'sender': 'send,1,127.0.0.1:12346,hello\n',
    'recipient': 'receive,2,1,127.0.0.1:12345,hello\n'
  },
  # Titles are only logged on the sending side and then added to the other side
  # when the logs are preprocessed. This is so that we don't have to send the
  # title over the wire or to force the user to provide the same title on both
  # sides of the connection.
  'udp_title_send': {
    'sender': 'send,1,127.0.0.1:12346,title,hello\n'
  },
  'udp_title_send_receive': {
    'sender': 'send,1,127.0.0.1:12346,title,hello\n',
    'recipient': 'receive,2,1,127.0.0.1:12345,hello\n'
  },
  'tcp_title_send_receive': {
    'sender': 'send,1,127.0.0.1:12346,title,hello\n',
    'recipient': 'receive,2,1,127.0.0.1:12345,hello\n'
  },
  'tcp_title_send_receive_duplex': {
    'sender':
      'send,1,127.0.0.1:12346,sender-title,sender-payload\n' +
      'receive,2,1,127.0.0.1:12346,recipient-payload\n',
    'recipient':
      'send,1,127.0.0.1:12345,recipient-title,recipient-payload\n' +
      'receive,2,1,127.0.0.1:12345,sender-payload\n'
  },
  'single_log_event': {
    'sender': 'log,1,hello\n'
  },
  'multiple_log_event': {
    'sender': 'log,1,hello123\n'
  },
  'single_log_title_event': {
    'sender': 'log,1,title,hello\n'
  },
  'multiple_log_title_event': {
    'sender': 'log,1,title,hello123\n'
  },
  'tcp_receive_empty_payload': {
    'recipient': ''
  }
}

class ProxyTestCase(unittest.TestCase):
  def performTest(self, testName):
    processes = []
    for vessel in ['recipient', 'sender']:
      logFile = join('tests', vessel, 'seastorm.log')
      if os.path.isfile(logFile):
        os.unlink(logFile)
      
      codeFile = join('tests', vessel, testName + '.repy')
      if os.path.isfile(codeFile):
        userCode = open(codeFile).read()
        libraryCode = open(join('..', 'client', 'seastorm_repy_wrapper.repy')).read()
        base64Stub = 'def seastorm_base64(s): return s'
        code = libraryCode + '\n\n' + base64Stub + '\n\n' + userCode
        testFile = join('tests', vessel, testName + '.test.repy')
        open(testFile, 'w').write(code)
        
        p = subprocess.Popen([
          'python',
          join('..', 'nodemanager', 'repyV2', 'repy.py'),
          join('..', 'restrictions.test'),
          testName + '.test.repy'
        ], cwd=join('tests', vessel))
        processes.append(p)
    
    time.sleep(10)
    
    for vessel in ['recipient', 'sender']:
      logFile = join('tests', vessel, 'seastorm.log')
      if vessel in expectations[testName]:
        log = open(logFile).read()
        self.assertEqual(log, expectations[testName][vessel])

def addTestMethod(testName):
  setattr(ProxyTestCase, 'test_' + testName, lambda self: self.performTest(testName))

for testName in expectations.keys():
  if len(sys.argv) < 2 or sys.argv[1] == testName:
    addTestMethod(testName)

# The main function inside unittest makes use of sys.argv for some purpose
# unless we override it here.
unittest.main(argv=sys.argv[:1])