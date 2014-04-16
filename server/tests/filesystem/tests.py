import os
import sys
import unittest

from os.path import join

sys.path.append('../../source')
import seastorm_watch_filesystem

class FilesystemTestCase(unittest.TestCase):
  def setUp(self):
    self.events = []
    
    def emit(event):
      self.events.append(event)
    
    self.poll = seastorm_watch_filesystem.watch('files', emit)
  
  def tearDown(self):
    for filename in os.listdir('files'):
      try:
        os.remove(join('files', filename))
      except:
        pass
  
  def testExistingFile(self):
    with open(join('files' , 'test.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    self.assertEqual(len(self.events), 1)
    self.assertEqual(self.events[0], 'test.txt')
  
  def testMultipleExistingFiles(self):
    with open(join('files', 'first.txt'), 'w') as f:
      f.write('contents')
      
    with open(join('files', 'second.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    self.assertEqual(len(self.events), 2)
    self.assertEqual(self.events[0], 'first.txt')
    self.assertEqual(self.events[1], 'second.txt')
  
  def testNewFile(self):
    self.poll()
    
    with open(join('files' , 'test.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    self.assertEqual(len(self.events), 1)
    self.assertEqual(self.events[0], 'test.txt')
  
  def testMultipleNewFiles(self):
    self.poll()
    
    with open(join('files', 'first.txt'), 'w') as f:
      f.write('contents')
      
    with open(join('files', 'second.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    self.assertEqual(len(self.events), 2)
    self.assertEqual(self.events[0], 'first.txt')
    self.assertEqual(self.events[1], 'second.txt')
    
  def testModifiedFile(self):
    with open(join('files', 'test.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    with open(join('files', 'test.txt'), 'w') as f:
      f.write('new contents')
      
    self.poll()
    
    self.assertEqual(len(self.events), 2)
    self.assertEqual(self.events[0], 'test.txt')
    self.assertEqual(self.events[1], 'test.txt')
  
  def testMultipleModifiedFiles(self):
    with open(join('files', 'first.txt'), 'w') as f:
      f.write('contents')
      
    with open(join('files', 'second.txt'), 'w') as f:
      f.write('contents')
      
    self.poll()
    
    with open(join('files', 'first.txt'), 'w') as f:
      f.write('new contents')
      
    with open(join('files', 'second.txt'), 'w') as f:
      f.write('new contents')
    
    self.poll()
    
    self.assertEqual(len(self.events), 4)
    self.assertEqual(self.events[2], 'first.txt')
    self.assertEqual(self.events[3], 'second.txt')
  
  def testRemovedFile(self):
    with open(join('files', 'test.txt'), 'w') as f:
      f.write('contents')
    
    self.poll()
    
    os.remove(join('files', 'test.txt'))
    
    self.poll()
    
    self.assertEqual(len(self.events), 2)
    self.assertEqual(self.events[1], 'test.txt')
  
unittest.main()