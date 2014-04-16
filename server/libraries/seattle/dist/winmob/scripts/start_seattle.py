"""
<Program Name>
  start_seattle.py

<Started>
  January 27, 2009

<Author>
  Carter Butaud

<Purpose>
  Starts the seattle node manager and software updater on 
  a device with Windows Mobile.
"""

import windows_api
import os

def start_seattle(prog_dir):
  """
  <Purpose>
    Launches the python processes necessary for seattle. Uses
    windows_api.launch_python_script for mobile portability.

  <Arguments>
    prog_dir:
      The directory which contains the seattle python scripts.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  windows_api.launch_python_script(prog_dir + "/nmmain.py")
  windows_api.launch_python_script(prog_dir + "/softwareupdater.py")



def main():
  start_seattle(os.getcwd())


if __name__ == "__main__":
  main()
