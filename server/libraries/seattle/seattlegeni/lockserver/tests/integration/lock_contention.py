"""
   Author: Justin Samuel

   Start Date: 30 June 2009

   Description:

   This test starts the lockserver and uses multiple threads, each acting as a
   different lockserver client, to communicate with the lockserver. The requests
   result in contention for some locks and cause some of the requests to block.
   
   Each method of the lockserver is used at least once in a correct fashion (that
   is, this test does not test invalid requests).
"""

# Add to the path the directory that the lockserver module is in ('../').
# This assumes that the script will be run from the tests/ directory which
# is one directory below where the lockserver_daemon.py file is.
import sys
sys.path.append('..')

import lockserver_daemon as lockserver

import threading
import xmlrpclib
import time



LOCKSERVER_URL = "http://localhost:8010"

# How long to wait (in seconds) for the test to finish before giving up.
TIMEOUT = 5.0

# Minimum time to wait (in seconds) for any action that requires giving
# another thread a chance to do something.
SLEEP_TIME = 0.5

events = {}

events['first_client_first_request_finished'] = threading.Event()
events['second_client_about_to_make_first_request'] = threading.Event()
events['second_client_about_to_release_locks'] = threading.Event()
  
error_occurred = False


def report_error(message=None):
  global error_occurred
  error_occurred = True
  
  print message




class LockserverThread(threading.Thread):
  
  def run(self):
    lockserver.main()





class BaseClientThread(threading.Thread):
  
  proxy = xmlrpclib.ServerProxy(LOCKSERVER_URL)
  

  def run(self):
    try:
      # do_work() must be implemented by subclasses
      self.do_work()
      
    except Exception:
      report_error()
      raise




class FirstClientThread(BaseClientThread):
  
  def do_work(self):
    
    # This will be the first request made by any client, so it doesn't wait
    # for any event.
    print "First client started."
    
    session_id = self.proxy.StartSession()
    print "First client assigned session_id: " + session_id
    
    locks = {'user':['bob']}
    
    print "First client acquiring locks: " + str(locks)
    self.proxy.AcquireLocks(session_id, locks)
    print "First client acquired locks: " + str(locks)

    events["first_client_first_request_finished"].set()
    
    # Give the second and third clients a chance to make blocking requests
    # for the same lock.
    time.sleep(SLEEP_TIME * 3)
    
    print "First client releasing locks: " + str(locks)
    self.proxy.ReleaseLocks(session_id, locks)
    
    print "First client ending session"
    self.proxy.EndSession(session_id)
    
      



class SecondClientThread(BaseClientThread):
  
  def do_work(self):
    
    events["first_client_first_request_finished"].wait()
    
    print "Second client started."
    
    session_id = self.proxy.StartSession()
    print "Second client assigned session_id: " + session_id
    
    # The third client will wait for some time after this event is set
    # before it starts making lock requests.
    events["second_client_about_to_make_first_request"].set()

    # Request the same lock already held by the first client.
    locks = {'user':['bob']}
    
    print "Second client acquiring locks: " + str(locks)
    self.proxy.AcquireLocks(session_id, locks)
    print "Second client acquired locks: " + str(locks)
    
    # The above AcquireLocks call will block until
    # the lock is obtained.
    
    events["second_client_about_to_release_locks"].set()
    
    print "Second client releasing locks: " + str(locks)
    self.proxy.ReleaseLocks(session_id, locks)
    
    print "Second client ending session"
    self.proxy.EndSession(session_id)
    
      
      


class ThirdClientThread(BaseClientThread):
  
  def do_work(self):
    
    events["second_client_about_to_make_first_request"].wait()
    
    # Give the second client a chance to make its requests.
    time.sleep(SLEEP_TIME)

    print "Third client started."
    
    session_id = self.proxy.StartSession()
    print "Third client assigned session_id: " + session_id
    
    # Request the same lock already held by the first client and already being
    # waited for by the second client. Request multiple user locks just to make
    # it more interesting.
    locks = {'user':['bob', 'alice']}
    
    print "Third client acquiring locks: " + str(locks)
    self.proxy.AcquireLocks(session_id, locks)
    print "Third client acquired locks: " + str(locks)
    
    # The above AcquireLocks call will block until
    # the lock is obtained.
    
    # This event wait for the second client to release locks is to ensure that
    # the test will fail if the third client acquired its locks before the second
    # client. If that were to happen (that is, if the lock queue wasn't processed
    # in the correct order, for example), this event will never get set and
    # the test will timeout.
    events["second_client_about_to_release_locks"].wait()
    
    print "Third client releasing locks: " + str(locks)
    self.proxy.ReleaseLocks(session_id, locks)
    
    # Have this client acquire and release the same locks a few more times.
    print "Third client acquiring/releasing the following locks a few times and holding on to them in the end: " + str(locks)
    self.proxy.AcquireLocks(session_id, locks)
    self.proxy.ReleaseLocks(session_id, locks)
    self.proxy.AcquireLocks(session_id, locks)
    
    # Have this client acquire and release some node locks while they hold the user locks.
    nodelocks = {'node':['123', '456']}
    print "Third client acquiring/releasing the following locks a few times: " + str(nodelocks)
    self.proxy.AcquireLocks(session_id, nodelocks)
    self.proxy.ReleaseLocks(session_id, nodelocks)
    self.proxy.AcquireLocks(session_id, nodelocks)
    self.proxy.ReleaseLocks(session_id, nodelocks)
    
    print "Third client releasing locks: " + str(locks)
    self.proxy.ReleaseLocks(session_id, locks)
    
    print "Third client ending session"
    self.proxy.EndSession(session_id)
    
    print "Third client calling GetStatus()"
    status = self.proxy.GetStatus()
    
    expected_heldlockdict = {'node': {'123': {'queue': [], 'locked_by_session': None},
                                      '456': {'queue': [], 'locked_by_session': None}}, 
                             'user': {'bob': {'queue': [], 'locked_by_session': None},
                                      'alice': {'queue': [], 'locked_by_session': None}}}
    if status["heldlockdict"] != expected_heldlockdict:
      report_error("The heldlockdict returned from GetStatus() was not as expected: " + str(status["heldlockdict"]))
      
    expected_sessiondict = {}
    if status["sessiondict"] != expected_sessiondict:
      report_error("The sessiondict returned from GetStatus() was not as expected: " + str(status["sessiondict"]))





def fail_if_thread_alive_after_timeout(clientthread):
  
  clientthread.join(TIMEOUT)

  # If the thread is still alive after TIMEOUT seconds, it's blocked and
  # so the test failed.
  if clientthread.isAlive():
    print "A client thread is still alive after the TIMEOUT expired."
    print "Assuming the test failed (the client is probably blocked)."
    sys.exit(1)
    
    
    


def main():
  # Start the lockserver.
  LockserverThread().start()
  
  # Give the lockserver time to start.
  time.sleep(SLEEP_TIME)

  # Start the clients.
  firstclientthread = FirstClientThread()
  firstclientthread.start()
  
  secondclientthread = SecondClientThread()
  secondclientthread.start()
  
  thirdclientthread = ThirdClientThread()
  thirdclientthread.start()
  
  fail_if_thread_alive_after_timeout(firstclientthread)
  fail_if_thread_alive_after_timeout(secondclientthread)
  fail_if_thread_alive_after_timeout(thirdclientthread)
    
  if error_occurred:
    print "An error occurred. Test failed."
    sys.exit(1)
    
  # The lockserver thread is still alive at this point and will be killed when
  # the main thread exits.
  print "Test passed."
  sys.exit(0)
  
  

if __name__ == "__main__":
  main()
