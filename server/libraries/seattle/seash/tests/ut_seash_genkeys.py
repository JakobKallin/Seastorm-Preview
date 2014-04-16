"""
Generates a series of keys and make sures the function is taking 
in arguments correctly.
"""
import seash
import os.path
import sys

orig_stdout = sys.stdout
sys.stdout = open("test_results.txt", "w")

command_list = [
  "genkeys joe", 
  "genkeys bob 50", 
  "genkeys sam as john", 
  "loadkeys sam", 
  "as sam", 
  "loadkeys sam", 
  "as john"
  ]

seash.command_loop(command_list)

sys.stdout.close()

sys.stdout = orig_stdout


# Compares the output with the expected output in the provided txt file.
# Results should hold a few simple lines such as "Identity bob has been created"
test_results = open("test_results.txt", "r")
wanted_results = open("genkeys_test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i].startswith(actual[i]):
    print "Line " + str(i) + " of test results are not consistent with expected results: genkeys_test_results.txt"

test_results.close()
wanted_results.close()



# Check that the created keys total character count is at least less than 60
testpublickey = open('bob.publickey')
testprivatekey = open('bob.privatekey')

publickey = testpublickey.readline()
privatekey = testprivatekey.readline()

publickeylist = publickey.split()
if not len(publickeylist[1]) + len(privatekey) < 60:
  print "Length of generated key 'bob' is far greater than expected"

os.remove("joe.publickey")
os.remove("joe.privatekey")

