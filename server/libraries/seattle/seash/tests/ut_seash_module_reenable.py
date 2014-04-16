"""
Make sure that the re-enable notice is visible to the user on launch
"""
import sys
import subprocess

seash_process = subprocess.Popen([sys.executable, 'seash.py'], 
    stdin=subprocess.PIPE, 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE)

# Terminate seash...
seash_process.stdin.write('exit\n')
seash_process.stdin.close()

# Windows machines output \r\n, not \n for newlines.
# Replace them so we don't have to test for 2 cases.
stdout = seash_process.stdout.read().replace('\r\n', '\n')
stderr = seash_process.stderr.read().replace('\r\n', '\n')

expected_out = """Enabled modules: modules"""

# If we have any mismatched/unexpected output, print them to the relevant streams
if expected_out not in stdout:
  print stdout

if stderr:
  print>>sys.stderr, stderr