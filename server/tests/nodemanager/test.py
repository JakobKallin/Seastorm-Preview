import sys
sys.path.append('../portability')
sys.path.append('../repy')

from repyportability import *
add_dy_support(locals())
dy_import_module_symbols('nmclient.repy')

def test_create_handle(ip, port):
	handle = nmclient_createhandle(ip, port)
	handle_info = nmclient_get_handle_info(handle)
	handle_info['publickey'] = public_key
	handle_info['privatekey'] = private_key
	nmclient_set_handle_info(handle, handle_info)
	return handle

ip_one = '192.168.2.2'
port_one = 1224

public_key = rsa_string_to_publickey(open('../../keys/test.publickey').read())
private_key = rsa_string_to_privatekey(open('../../keys/test.privatekey').read())

time_updatetime(12345)

handle_one = test_create_handle(ip_one, port_one)

nmclient_signedsay(handle_one, 'AddFileToVessel', 'v1', 'foo.txt', 'This is foo!')
