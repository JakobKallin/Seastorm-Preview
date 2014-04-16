# This file is part of Seastorm
# Copyright 2014 Jakob Kallin

import sys
sys.path.append('../libraries')

import BaseHTTPServer
import requests
import sys
import json

class ClearinghouseHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	allowed_origin = 'http://seastorm.localhost'
	clearinghouse_host = 'seattleclearinghouse.poly.edu'
	clearinghouse_path = '/xmlrpc/'
	
	def do_OPTIONS(self):
		self.send_response(200)
		self.send_cors_headers()
		self.end_headers()
	
	def do_POST(self):
		body = self.get_body()
		response = self.make_request(body)
		
		self.send_response(response.status_code)
		# The Clearinghouse API does not set `Content-Type` to `text/xml`, so
		# let's override that here in order to make things easier for the
		# JavaScript. (The browser doesn't automatically parse the XML unless
		# the response has the correct `Content-Type` header.)
		self.send_header('Content-Type', 'text/xml')
		self.send_cors_headers()
		self.end_headers()
		
		self.wfile.write(response.text)
	
	def get_body(self):
		content_length = int(self.headers.getheader('Content-Length'))
		request_body = self.rfile.read(content_length)
		return request_body
	
	def make_request(self, body):
		url = 'https://' + self.clearinghouse_host + self.clearinghouse_path
		headers = {'Content-Type': 'text/xml'}
		response = requests.post(url, data=body, headers=headers, verify=True)
		return response
	
	def send_cors_headers(self):
		self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
		self.send_header('Access-Control-Allow-Headers', 'Content-Type')

def start():
	host = 'localhost'
	port = 5346
	
	server = BaseHTTPServer.HTTPServer((host, port), ClearinghouseHandler)
	
	try:
		print 'Starting clearinghouse proxy'
		server.serve_forever()
	except KeyboardInterrupt:
		print 'Stopping clearinghouse proxy'	
		server.server_close()