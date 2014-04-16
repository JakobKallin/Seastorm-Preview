# This file is part of Seastorm
# Copyright 2014 Jakob Kallin

import sys
sys.path.append('../portability')
sys.path.append('../repy')

from repyportability import *
add_dy_support(locals())
dy_import_module_symbols('nmclient.repy')

import threading

class NodeManager():
	def __init__(self):
		self.handle_table = {}
		self.handle_lock_table = {}
		self.handle_creation_lock = threading.Lock()
		time_updatetime(12345)
	
	def call(self, ip, port, public_key, private_key, function_name, argument_table):
		argument_list = self.get_argument_list(function_name, argument_table)
		return self.call_nmclient(public_key, private_key, ip, port, function_name, argument_list)
	
	def get_argument_list(self, function_name, argument_table):
		argument_names = self.get_argument_names(function_name)
		try:
			return [argument_table[key] for key in argument_names]
		except KeyError:
			raise ValueError(
				"The required arguments %s have not been provided,"
				% argument_names
			)
	
	def get_argument_names(self, function_name):
		argument_name_table = {
			  'GetVessels': []
			, 'GetVesselResources': ['vesselname']
			, 'GetOffcutResources': []
			, 'StartVessel': ['vesselname', 'args']
			, 'StartVesselEx': ['vesselname', 'program_platform', 'args']
			, 'StopVessel': ['vesselname']
			, 'AddFileToVessel': ['vesselname', 'filename', 'filedata']
			, 'RetrieveFileFromVessel': ['vesselname', 'filename']
			, 'DeleteFileInVessel': ['vesselname', 'filename']
			, 'ReadVesselLog': ['vesselname']
			, 'ListFilesInVessel': ['vesselname']
			, 'ResetVessel': ['vesselname']
		}
		
		if function_name in argument_name_table:
			return argument_name_table[function_name]
		else:
			raise ValueError(
				"The node manager function '%s' does not exist or is not supported."
				% function_name
			)

	def call_nmclient(self, public_key, private_key, ip, port, function_name, arguments):
		public_functions = [
			  'GetVessels'
			, 'GetVesselResources'
			, 'GetOffcutResources'
		]
		
		# Lock before creating handles, because we only want a single handle for
		# every IP+port combination.
		self.handle_creation_lock.acquire()
		try:
			if (ip, port) not in self.handle_table:
				self.handle_table[ip, port] = self.create_nm_handle(ip, port, public_key, private_key)
				self.handle_lock_table[ip, port] = threading.Lock()
		finally:
			self.handle_creation_lock.release()
		
		handle = self.handle_table[ip, port]
		handle_lock = self.handle_lock_table[ip, port]
		
		# Lock before using the handle for this specific IP+port combination,
		# because using handles concurrently causes "Timestamps match" errors.
		handle_lock.acquire()
		try:
			if function_name in public_functions:
				result = nmclient_rawsay(handle, function_name, *arguments)
			else:
				result = nmclient_signedsay(handle, function_name, *arguments)
		finally:
			handle_lock.release()
		
		return result
	
	def create_nm_handle(self, ip, port, public_key, private_key):
		handle = nmclient_createhandle(ip, port)
		handle_info = nmclient_get_handle_info(handle)
		handle_info['publickey'] = rsa_string_to_publickey(public_key)
		handle_info['privatekey'] = rsa_string_to_privatekey(private_key)
		nmclient_set_handle_info(handle, handle_info)
		return handle