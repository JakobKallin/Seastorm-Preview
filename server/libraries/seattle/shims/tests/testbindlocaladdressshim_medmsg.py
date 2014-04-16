dy_import_module_symbols("testgeneralshim_helper")

# Choose a random ip address and use BindLocalAddressShim to change to 
# the correct ip address, and it should work.

CLIENT_IP = "145.65.8.245"
CLIENT_PORT = 72689

SERVER_SHIM_STRING = "(NoopShim)"
CLIENT_SHIM_STRING = "(BindLocalAddressShim,%s:%d)" % (getmyip(), 34256)


# Test data size of 10 MB
DATA_TO_SEND = "HelloWorld" * 1024 * 1024

RECV_SIZE = 2**14 # 16384 bytes.
END_TAG = "@@END"
SLEEP_TIME = 0.01

launch_test()
