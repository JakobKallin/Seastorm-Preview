dy_import_module_symbols("testcompressionshim_helper")

SERVER_IP = getmyip()
SERVER_PORT = 34829

# Test data size of 10 MB
DATA_TO_SEND = "HelloWorld" * 1024 * 1024

RECV_SIZE = 2**14 # 16384 bytes.
END_TAG = "@@END"
SLEEP_TIME = 0.001

# Shim string to use for server and client
# Note that we add the CheckApiShim to the Default Shim String such that
# the CheckApiShim does not have any impact on the tests itself, especially
# when calculating the upload and download rate.
#
# If possible the CoordinationShim and CheckApiShim should always be part
# of both the shim strings.
SHIM_STRING_SERVER = "(CoordinationShim)(CompressionShim)(CheckApiShim)"
SHIM_STRING_SERVER_DEFAULT = "(CoordinationShim)(NoopShim)(CheckApiShim)"

SHIM_STRING_CLIENT = "(CoordinationShim)"

launch_test()
