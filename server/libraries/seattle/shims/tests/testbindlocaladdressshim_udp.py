dy_import_module_symbols("udptest_helper")

CLIENT_IP = "156.255.54.98" # Fake IP address
SERVER_IP = getmyip()
SERVER_PORT = 35742
SEND_PORT = 90 # Priviledged port.


SERVER_SHIM_STR = "(NoopShim)"
CLIENT_SHIM_STR = "(BindLocalAddressShim,%s:%d)" % (getmyip(), 34567) 

launch_test(SERVER_SHIM_STR, CLIENT_SHIM_STR)
