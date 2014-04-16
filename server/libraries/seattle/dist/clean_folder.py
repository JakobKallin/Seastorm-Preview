"""
<Program Name>
  clean_folder.py

<Started>
  September, 2008
    Amended June 23, 2009

<Author>
  Carter Butaud
    Amended by Zachary Boka

<Purpose>
  Parses an instructions file and uses it to check/clean a directory.
  The instructions file should have the following format:
    
    req required_file_1
    req at_least, one_of_these, is_required
    
    del bad_file
    del *.pyc
    del bad_file_number?

    # This line is a comment
    req file_4 # Comments can be inline

  Invalid lines in instructions files (non-empty lines that do not start with
  "req", "del", or "#") will cause warnings to be printed.  Files in directory
  that are not listed in the instructions file while be printed as warnings. 
  If one file is both required and deleted, the program quits with a ParseError.
"""

import os
import re
import sys

class IllegalArgError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ParseError(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# For now, simply prints the given string. I made it a function in case we want
# to allow a silent run later on
def output(text):
  print text

# Given the name of a file, it will scan the file for lines starting with "req"
# or "del", ignoring lines commented with '#', and return two arrays containing
# the lines that followed req and the lines that followed del. Prints warnings
# for any lines that do not meet these criteria, but runs anyway.
def parse_instructions(instr_path):
  instr_file = open(instr_path)
  req_files = []
  del_files = []
  line_count = 0
  for line in instr_file:
    line_count += 1
    # Filter out newlines
    line = re.sub("\n", "", line)
    # Filter out comments
    line = re.sub(r"#.*", "", line)
    # Escape periods
    line = re.sub(r"\.", r"\.", line)
    # Replace wildcards with nearest regex equivalent
    line = re.sub(r"\*", ".*", line)
    line = re.sub(r"\?", ".", line)
    if line:
      m = re.match("^req (.*)", line)
      m2 = re.match("^del (.*)", line)
      if m:
        req_files.append(m.group(1).strip())
      elif m2:
        del_files.append(m2.group(1).strip())
      else:
        output("Parse warning: skipping invalid line " + str(line_count) + " in "
                + instr_path)

  # Check that no file is both required and deleted
  # Zack: Unable to come up with a better algorithm for this at the moment
  for del_file in del_files:
    for req_file in req_files:
      for part in req_file.split(","):
        if part.strip() == del_file:
          raise ParseError("File both required and deleted: " + part)

  return (req_files, del_files)


                    
def clean_folder(instr_path, dir_to_clean):
  """
  <Purpose>
    Given an instructions file and a directory, it will make sure that
    the directory matches the instructions, deleting files where necessary,
    printing errors where files are missing, and printing warnings where
    unrecognized files exist.
    
  <Arguments>
    instr_path:
      The location of the instructions file to be used.
    dir_to_clean:
      The location of the directory to be cleaned.

  <Exceptions>
    IllegalArgError on bad filepaths.
    ParseError on invalid instructions file.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # First, get the required files and the files to be deleted
  (req_files, del_files) = parse_instructions(instr_path)
  req_files_found = [False for i in range(len(req_files))]
  unrecognized_files = []
  for filename in os.listdir(dir_to_clean):
    deleted = False
    for del_file in del_files:
      if re.match(del_file, filename):
        if del_file != ".*\.pyc" and filename.endswith(".pyc"):
          pass  # do nothing because the del_file ends in .py but will try the 
                # filename that will get deleted ends with .pyc (this was 
                # previously deleted and will thus cause an error if we try to
                # delete it again!).  BUG!!! Ticket
        else:
          deleted = True
          os.remove(dir_to_clean + "/" + filename)
    if not deleted:
      required = False
      for i in range(len(req_files)):
        for subfile in req_files[i].split(","):
          subfile = subfile.strip()
          if re.match(subfile, filename):
            req_files_found[i] = True
            required = True
      if not required:
        unrecognized_files.append(filename)
  for filename in unrecognized_files:
    output("Warning: unrecognized file " + filename)
  for i in range(len(req_files)):
    if not req_files_found[i]:
      output("Error: required file " + req_files[i] + " not found")



def main():
  if len(sys.argv) < 3 or len(sys.argv) > 3:
    output("usage: python clean_folder.py instructions.fi directory/to/clean/")
  else:
    if not os.path.exists(sys.argv[1]):
      raise IllegalArgError("Instructions file does not exist: " + sys.argv[1])
    elif not os.path.exists(sys.argv[2]):
      raise IllegalArgError("Given directory does not exist: " + sys.argv[2])
    else:
      clean_folder(sys.argv[1], sys.argv[2])
            

if __name__ == "__main__":
  main()
