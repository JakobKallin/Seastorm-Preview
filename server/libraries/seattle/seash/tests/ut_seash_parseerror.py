"""
A simple test to make sure seash's parser is catching wrong commands correctly.
"""

#pragma error Command not understood
import seash_dictionary

# Parser should recognize these commands as valid
seash_dictionary.parse_command("loadkeys notakey")
seash_dictionary.parse_command("show ip to example_file.txt")
seash_dictionary.parse_command("run example.1.1.repy example arguments")

# Parser should throw an error for following command
seash_dictionary.parse_command("incorrect command")
