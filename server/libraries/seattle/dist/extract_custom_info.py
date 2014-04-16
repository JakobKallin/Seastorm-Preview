"""
<Program Name>
  extract_custom_info.py

<Started>
  April 5, 2010

<Autho>
  Zachary Boka

<Purpose>
  Extract information from the end of a source file and append it to a
  destination file.

  This program was written to extract the customized installer information
  appended to the end of the Windows GUI installers and write it out to a newly 
  created vesselinfo file that this program creates.  This program is meant
  to be run at install time and is started by the GUI installer and not by
  seattleinstaller.py.
"""

import os
import os.path

SOURCE_FILE = os.path.realpath(".." + os.sep + ".." + os.sep \
                                 +"seattle_win_gui.exe")
DEST_FILE = os.path.realpath(".") + os.sep + "vesselinfo"
SPECIAL_SEQUENCE = "START:"
BLOCKSIZE = 4096 #Size of the blocks of the file that will be read in and out




def get_start_index(file_obj):
  """
  <Purpose>
    Finds the index in the passed-in file object of the last SPECIAL_SEQUENCE
    to appear in the file.

  <Arguments>
    file_obj: the file object for the file whose contents will be searched for
              the SPECIAL_SEQUENCE.

  <Exceptions>
    None.
    
  <Side Effects>
    None.

  <Returns>
    The index in the passed-in file object of the last SPECIAL_SEQUENCE to
    appear in the file.
  """

  # Initialize the buffer that will hold chunks of the file for scanning.
  buffer = ""
  temp_new__buffer = ""

  # Setup to start reading from the end of the file.
  file_obj.seek(0,os.SEEK_END)
  end_index = file_obj.tell()


  # Read contents backward from the installer file until the SPECIAL_SEQUENCE
  # is found.
  while True:
    # Keep track of the current position in the file.
    position = file_obj.tell()

    sequence_position = buffer.rfind(SPECIAL_SEQUENCE)

    if sequence_position != -1:
      # Found the SPECIAL_SEQUENCE, so return its index within the file of where
      # the SPECIAL_SEQUENCE starts.
      return position + sequence_position

    elif position:
      # Need to add more of the end of the file to the buffer because the
      # SPECIAL_SEQUENCE has not yet been found.

      # Replace the contents fo the buffer so that not more than BLOCKSIZE * 2
      # is stored in the buffer.  This prevents stack overflows if the contents
      # of the file is too large.  After reading in the very first BLOCKSIZE
      # worth of contents, there must be at least BLOCKSIZE * 2 contents in the
      # buffer in case the SPECIAL_SEQUENCE is straddling the boundary of two
      # BLOCKSIZE chunks.
      if temp_new_buffer != "":
        buffer = temp_new_buffer

      # Get min(BLOCKSIZE,position) so that we don't read off the beginning of 
      # the file.
      to_read = min(BLOCKSIZE,position)
      file_obj.seek(-to_read,os.SEEK_CUR)
      temp_new_buffer = file_obj.read(to_read)
      buffer = temp_new_buffer + buffer
      file_obj.seek(-to_read,os.SEEK_CUR)

    else:
      # Reached the start of the file and did not find the special sequence.
      return -1




def write_out_to_file(source_file_obj,dest_file_obj,start_index):
  """
  <Purpose>
    Writes the contents of the SOURCE_FILE starting after start_index to the
    DEST_FILE.

  <Arguments>
    source_file_obj: File object for the SOURCE_FILE.
    dest_file_obj: File object for the DEST_FILE.
    start_index: Index in the SOURCE_FILE of the contents that should be written
                 out to DEST_FILE.

  <Exceptions>
    None.

  <Side Effects>
    Writes BLOCKSIZE chunks from SOURCE_FILE to DEST_FILE.

  <Returns>
    None.
  """

  # Move to just past the SPECIAL_SEQUENCE in the file
  source_file_obj.seek(start_index,os.SEEK_SET)

  # Write out to the DEST_FILE in BLOCKSIZE chunks
  line = source_file_obj.read(BLOCKSIZE)
  while line != "":
    dest_file_obj.write(line)
    line = source_file_obj.read(BLOCKSIZE)




def main():

  # Remove the DEST_FILE if it already exists before creating its file object.
  # Data will be appended to the new DEST_FILE in chunks which is why it must
  # be removed ahead of time.
  if os.path.exists(DEST_FILE):
      os.remove(DEST_FILE)

  # Create the file objects.
  dest_file_obj = open(DEST_FILE,'a')
  source_file_obj = open(SOURCE_FILE,'rb')

  # Get the start index for the appended information from the SOURCE_FILE.
  start_index = get_start_index(source_file_obj)
  if start_index == -1:
    print "ERROR: Special sequence not found: " + SPECIAL_SEQUENCE
    return

  # Write out the appended information from the SOURCE_FILE to the DEST_FILE
  # after the SPECIAL_SEQUENCE.
  write_out_to_file(source_file_obj,dest_file_obj,
                    start_index + len(SPECIAL_SEQUENCE))

  # Close the file objects.
  source_file_obj.close()
  dest_file_obj.close()




if __name__ == "__main__":
  main()
