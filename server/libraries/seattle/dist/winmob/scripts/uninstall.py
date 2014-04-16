import os

STARTER_FILE = "%STARTER_FILE%"

def main():

  # Initialize the service logger.
  servicelogger.init('installInfo')

  if os.path.exists(STARTER_FILE):
    os.remove(STARTER_FILE)
    servicelogger.log(time.strftime(" seattle was UNINSTALLED on: %m-%d-%Y %H:%M:%S"))
    
if __name__ == "__main__":
  main()
