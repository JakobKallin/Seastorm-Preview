dy_import_module_symbols("testonehopdetour_tcp_helper")

SERVER_IP = getmyip()
SERVER_PORT = 34829

# Test data size of 10 MB
DATA_TO_SEND = "HelloWorld" 

RECV_SIZE = 2**14 # 16384 bytes.
END_TAG = "@@END"
SLEEP_TIME = 0.01

launch_test()
