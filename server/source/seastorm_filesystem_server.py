# This file is part of Seastorm
# Copyright 2014 Jakob Kallin

import BaseHTTPServer
import os
import time
import SocketServer
import sys
import urllib

from os.path import join

import seastorm_watch_filesystem

class FilesystemHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  allowedOrigin = 'http://seastorm.localhost'
  watchPath = None
  pollInterval = 1
  
  def do_OPTIONS(self):
    self.send_response(200)
    self.sendCorsHeaders()
    self.end_headers()
  
  def do_HEAD(self):
    if self.watchPath is None:
      self.sendError()
    else:
      self.send_response(200)
      self.sendCorsHeaders()
      if self.path == '/':
        self.send_header('Content-Type', 'text/event-stream')
      else:
        self.send_header('Content-Type', 'application/octet-stream')
      self.end_headers()
  
  def do_GET(self):
    if self.watchPath is None:
      self.sendError()
    elif self.path == '/':
      self.getEvents()
    else:
      self.getFile()
  
  def getEvents(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/event-stream')
    self.sendCorsHeaders()
    self.end_headers()
    
    def emit(filename):
      # Make sure that a filename with newlines does not break the event format
      # or inject events.
      escapedFilename = filename.replace('\n', '').replace('\r', '')
      self.wfile.write('data: ' + str(escapedFilename) + '\n\n')
    
    poll = seastorm_watch_filesystem.watch(self.watchPath, emit)
    
    while True:
      poll()
      time.sleep(self.pollInterval)
  
  def getFile(self):
    filename = urllib.unquote(self.path[1:]) # Remove leading slash.
    if filename in os.listdir(self.watchPath):
      filePath = join(self.watchPath, filename)
      self.sendFile(filePath)
    else:
      self.sendFileError()
  
  def sendFile(self, filename):
    self.send_response(200)
    self.send_header('Content-Type', 'application/octet-stream')
    self.sendCorsHeaders()
    self.end_headers()
    
    with open(filename) as f:
      contents = f.read()
    self.wfile.write(contents)
  
  def sendFileError(self):
    self.send_response(404)
    self.sendCorsHeaders()
    self.end_headers()
  
  def sendError(self):
    self.send_response(501)
    self.sendCorsHeaders()
    self.end_headers()
    
  def sendCorsHeaders(self):
    self.send_header('Access-Control-Allow-Origin', self.allowedOrigin)

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

def start(watchPath=None):
  host = 'localhost'
  port = 5347
  
  FilesystemHandler.watchPath = watchPath
  
  server = ThreadedHTTPServer((host, port), FilesystemHandler)
  
  try:
    print 'Starting filesystem server'
    server.serve_forever()
  except KeyboardInterrupt:
    print 'Stopping filesystem server'  
    server.server_close()