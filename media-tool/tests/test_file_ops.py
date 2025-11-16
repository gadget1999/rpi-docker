"""Tests for file operations."""
import unittest
import os
import tempfile
from utils.file_ops import handle_duplicates, scan_folder_recursive

class TestFileOps(unittest.TestCase):
  def test_handle_duplicates_counter(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      test_file = os.path.join(tmpdir, 'test.txt')
      with open(test_file, 'w') as f:
        f.write('test')
      
      # First call should return same path if file doesn't exist
      new_path = handle_duplicates(os.path.join(tmpdir, 'new.txt'), 'counter')
      self.assertEqual(new_path, os.path.join(tmpdir, 'new.txt'))
      
      # Second call with existing file should add counter
      new_path = handle_duplicates(test_file, 'counter')
      self.assertEqual(new_path, os.path.join(tmpdir, 'test_1.txt'))
  
  def test_handle_duplicates_skip(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      test_file = os.path.join(tmpdir, 'test.txt')
      with open(test_file, 'w') as f:
        f.write('test')
      
      # Should return None if file exists and strategy is skip
      new_path = handle_duplicates(test_file, 'skip')
      self.assertIsNone(new_path)

if __name__ == '__main__':
  unittest.main()
