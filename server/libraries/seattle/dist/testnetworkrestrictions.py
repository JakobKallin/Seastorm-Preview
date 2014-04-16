# Armon: This tests the installer's behavior when handling network restriction flags
# It does so by passing various flags to seattleinstaller.py and checking the generated nodeman.cfg file.
#
import persist
import subprocess
import os
import shutil

# Backup the original config file
def backup_config():
  os.rename("nodeman.cfg","nodeman.cfg.bak")

# Restores a copy of the config file
def restore_copy():
  # Delete the current version
  if os.path.exists("nodeman.cfg"):
    os.remove("nodeman.cfg")
  
  # Copy a version of the backup
  shutil.copyfile("nodeman.cfg.bak","nodeman.cfg")

# Launches seattleinstaller.py with arguments, returns the generated config
# Includes the --onlynetwork flag
def test_launch(arguments):
  # Setup a clean slate
  restore_copy()

  # Create the cmdline option
  command = "python seattleinstaller.py --onlynetwork "+arguments

  # Call subprocess
  proc = subprocess.Popen(command,shell=True)

  # Wait for the process to finish
  proc.wait()

  # Get the configuration
  config = persist.restore_object("nodeman.cfg")
 
  # Return the config
  return config

# Tests for the default settings
def test_default_settings():
  args = ""
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":False, "nm_user_preference":[], "repy_restricted":False, "repy_user_preference":[], "repy_nootherips":False} 
  return (config==expected, expected,config)

# Tests basic NM IP and Iface passing 
def test_basic_nm_settings():
  args = "--nm-ip 192.168.1.1 --nm-iface eth0 --nm-ip 127.0.0.1 --nm-iface lo"
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":True, "nm_user_preference":[(True, "192.168.1.1"),(False,"eth0"),(True,"127.0.0.1"),(False,"lo")], "repy_restricted":False, "repy_user_preference":[], "repy_nootherips":False} 
  return (config==expected, expected,config)

# Tests basic Repy IP and Iface passing 
def test_basic_repy_settings():
  args = "--repy-ip 192.168.1.1 --repy-iface eth0 --repy-ip 127.0.0.1 --repy-iface lo"
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":False, "nm_user_preference":[], "repy_restricted":True, "repy_user_preference":[(True, "192.168.1.1"),(False,"eth0"),(True,"127.0.0.1"),(False,"lo")], "repy_nootherips":False} 
  return (config==expected, expected,config)

# Tests Repy nootherip passing 
def test_repy_nootherips():
  args = "--repy-nootherips"
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":False, "nm_user_preference":[], "repy_restricted":True, "repy_user_preference":[], "repy_nootherips":True} 
  return (config==expected, expected,config)

# Tests more advanced Repy IP and Iface passing 
def test_adv_repy_settings():
  args = "--repy-ip 192.168.1.1 --repy-iface eth0 --repy-ip 127.0.0.1 --repy-iface lo --repy-nootherips"
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":False, "nm_user_preference":[], "repy_restricted":True, "repy_user_preference":[(True, "192.168.1.1"),(False,"eth0"),(True,"127.0.0.1"),(False,"lo")], "repy_nootherips":True} 
  return (config==expected, expected,config)

# Tests very convoluted argument 
def test_complex_settings():
  args = "--repy-ip 192.168.1.1 --nm-iface xl0 --repy-iface eth0 --nm-ip 192.168.2.1 --repy-ip 127.0.0.1 --repy-nootherips --nm-iface eth0 --repy-iface lo"
  config = test_launch(args)
  config = config["networkrestrictions"]
  expected = {"nm_restricted":True, "nm_user_preference":[(False, "xl0"),(True,"192.168.2.1"),(False,"eth0")], "repy_restricted":True, "repy_user_preference":[(True, "192.168.1.1"),(False,"eth0"),(True,"127.0.0.1"),(False,"lo")], "repy_nootherips":True} 
  return (config==expected, expected,config)


# Runs a given test and logs things
def run_test(test):
  print "Running Test:",test.func_name
  # Run the test
  try:
    (success, expected, received) = test()
  except Exception, e:
    success = False
    expected = "Unknown! Test Raised Exception."
    received = "Exception:"+str(e)

  # Check for failure   
  if not success:
    print "Failure! Expected:",expected,"Received:",received

TO_RUN = [test_default_settings, test_basic_nm_settings, test_basic_repy_settings,test_repy_nootherips,test_adv_repy_settings,test_complex_settings]

def main():
  # Backup the config file
  backup_config()
  
  # Run each test
  for test in TO_RUN:
    run_test(test)
  
  # Restore the file
  restore_copy()

if __name__ == "__main__":
  main()
