# This file is part of Seastorm
# Copyright 2014 Jakob Kallin

import sys
import subprocess
import threading

import seastorm_clearinghouse_proxy
import seastorm_filesystem_server
import seastorm_node_manager_proxy

def start(key_path, watch_path=None):
	class ClearinghouseThread(threading.Thread):
		def run(self):
			seastorm_clearinghouse_proxy.start()
	
	class NodeManagerThread(threading.Thread):
		def run(self):
			public_key_file = key_path + '.publickey'
			private_key_file = key_path + '.privatekey'
			seastorm_node_manager_proxy.start(
				public_key_file=public_key_file,
				private_key_file=private_key_file
			)
	
	class FilesystemThread(threading.Thread):
		def run(self):
			seastorm_filesystem_server.start(watch_path)
	
	threads = [
		ClearinghouseThread(),
		NodeManagerThread(),
		FilesystemThread()
	]
	
	for t in threads:
		t.start()
	
	for t in threads:
		t.join()

if __name__ == '__main__':
	args = sys.argv[1:]
	if len(args) == 2:
		start(
			key_path=args[0],
			watch_path=args[1]
		)
	elif len(args) == 1:
		start(
			key_path=args[0],
			watch_path=None
		)
	else:
		print 'Usage: server.py key_path file_directory'