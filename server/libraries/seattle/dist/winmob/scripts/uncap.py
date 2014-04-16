"""
<Program Name>
  uncap.py
  
<Started>
  March 10, 2009
  
<Author>
  Carter Butaud
  
<Purpose>
  Uncapitalizes the filenames of all files in a given directory.
"""

import os

def uncap(dir, recursive=False):
  """
  <Purpose>
    Uncapitalizes the filenames of every file located in the given directory
    (and subdirectories, if specified).
  
  <Arguments>
    dir:
      The directory containing the files and/or subdirectories which should be uncapitalized.
    recursive:
      If True, operates on subdirectories as well.
      If False, operates only on the current directory.
      Defaults to False.
  
  <Exceptions>
    IOError on bad filepath.
  
  <Side Effects>
    None.
  
  <Returns>
    None.
  """
  files = os.listdir(dir)
  for fn in files:
    oldfilepath = dir + os.sep + fn
    newfilepath = dir + os.sep + fn.lower()
    if oldfilepath != newfilepath and not os.path.isdir(oldfilepath):
      # It's just a file, not a directory, so go ahead and rename it
      os.rename(oldfilepath, newfilepath)
    elif recursive and oldfilepath != newfilepath:
      # If it is a directory, and we ought to operate on directories
      os.rename(oldfilepath, newfilepath)
      uncap(newfilepath, True)


def main():
  uncap(os.getcwd(), True)


if __name__ == "__main__":
  main()  
  