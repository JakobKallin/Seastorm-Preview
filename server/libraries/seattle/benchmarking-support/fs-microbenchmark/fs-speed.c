// This program benchmarks the file I/O speed of C when creating, 
// deleting, reading, and writing file data.

#include<stdio.h>
#include<stdlib.h>
#include<time.h>

const int CREATE_FILE_COUNT = 10000;
const int READ_WRITE_COUNT = 10000;
const int READ_WRITE_BLOCK_SIZE = 1024;

int main(void) {
  printf("This needs work and I need to move on.   Someone please take a look!\n");

/*
#### Creation
beforetime = time.time()
for filenumber in range(CREATE_FILE_COUNT):
  open('benchmarkfile.'+str(filenumber),'w').close()

aftertime = time.time()
print 'Time to create '+str(CREATE_FILE_COUNT)+' files: ',aftertime - beforetime


#### Deletion
beforetime = time.time()
for filenumber in range(CREATE_FILE_COUNT):
  os.remove('benchmarkfile.'+str(filenumber))

aftertime = time.time()
print 'Time to delete '+str(CREATE_FILE_COUNT)+' files: ',aftertime - beforetime


#### Write
fo = open('benchmarkfile.rw','w+')
beforetime = time.time()
for writecount in range(READ_WRITE_COUNT):
  fo.write('X' *  READ_WRITE_BLOCK_SIZE)

aftertime = time.time()
print 'Time to write '+str(READ_WRITE_COUNT)+' blocks of size '+str(READ_WRITE_BLOCK_SIZE)+': ',aftertime - beforetime


#### READ
fo.seek(0)
beforetime = time.time()
for readcount in range(READ_WRITE_COUNT):
  fo.read(READ_WRITE_BLOCK_SIZE)

aftertime = time.time()
print 'Time to read '+str(READ_WRITE_COUNT)+' blocks of size '+str(READ_WRITE_BLOCK_SIZE)+': ',aftertime - beforetime

fo.close()

os.remove('benchmarkfile.rw')
*/

  return 0;
}
