# This file is part of Seastorm
# Copyright 2014 Jakob Kallin

import os
from os.path import join

def watch(watchPath, emit):
  lastModified = {}
  
  def poll():
    # Check existing files for changes.
    for filename in os.listdir(watchPath):
      filePath = join(watchPath, filename)
      if os.path.isfile(filePath):
        fileTime = os.stat(filePath).st_mtime
        if filename not in lastModified or fileTime > lastModified[filename]:
          emit(filename)
        
        lastModified[filename] = fileTime
    
    # Check if previously existing files have been removed.
    for filename in lastModified.keys():
      filePath = join(watchPath, filename)
      if not os.path.isfile(filePath):
        emit(filename)
        lastModified.pop(filename, None)
  
  return poll