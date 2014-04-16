dy_import_module_symbols("udptest_helper")

SHIM_STR = "(UdpMultiPipeShim,12346,(FECShim),12345)(NoopShim)"

launch_test(SHIM_STR, SHIM_STR)
