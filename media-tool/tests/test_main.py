"""Tests for main.py utility functions."""
import unittest
import tempfile
import os
from config_loader import ConfigLoader
from main import apply_camera_model_mapping

class TestCameraModelMapping(unittest.TestCase):
  def test_exact_match(self):
    config_content = """
source_folder: "/test"
staging_folder: "/test"
log_file: "/test/log.txt"
photo:
  max_width: 3840
  max_height: 2160
  extensions: [".jpg"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
camera_model_mapping:
  "Canon EOS 350D": "350D"
  "iPhone 16 Pro": "iPhone16Pro"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
      f.write(config_content)
      config_path = f.name
    
    try:
      config = ConfigLoader(config_path)
      
      # Test exact match
      result = apply_camera_model_mapping("Canon EOS 350D", config)
      self.assertEqual(result, "350D")
      
      result = apply_camera_model_mapping("iPhone 16 Pro", config)
      self.assertEqual(result, "iPhone16Pro")
    finally:
      os.remove(config_path)
  
  def test_case_insensitive_match(self):
    config_content = """
source_folder: "/test"
staging_folder: "/test"
log_file: "/test/log.txt"
photo:
  max_width: 3840
  max_height: 2160
  extensions: [".jpg"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
camera_model_mapping:
  "Canon EOS 350D": "350D"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
      f.write(config_content)
      config_path = f.name
    
    try:
      config = ConfigLoader(config_path)
      
      # Test case insensitive
      result = apply_camera_model_mapping("canon eos 350d", config)
      self.assertEqual(result, "350D")
    finally:
      os.remove(config_path)
  
  def test_no_mapping_cleanup(self):
    config_content = """
source_folder: "/test"
staging_folder: "/test"
log_file: "/test/log.txt"
photo:
  max_width: 3840
  max_height: 2160
  extensions: [".jpg"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
camera_model_mapping:
  "Canon EOS 350D": "350D"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
      f.write(config_content)
      config_path = f.name
    
    try:
      config = ConfigLoader(config_path)
      
      # Test unmapped model - should clean up spaces
      result = apply_camera_model_mapping("Sony Alpha 7R V", config)
      self.assertEqual(result, "SonyAlpha7RV")
      
      # Test with slashes
      result = apply_camera_model_mapping("Nikon D850/D810", config)
      self.assertEqual(result, "NikonD850_D810")
    finally:
      os.remove(config_path)
  
  def test_empty_model(self):
    config_content = """
source_folder: "/test"
staging_folder: "/test"
log_file: "/test/log.txt"
photo:
  max_width: 3840
  max_height: 2160
  extensions: [".jpg"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
      f.write(config_content)
      config_path = f.name
    
    try:
      config = ConfigLoader(config_path)
      
      # Test empty/None model
      result = apply_camera_model_mapping("", config)
      self.assertEqual(result, "Unknown")
      
      result = apply_camera_model_mapping(None, config)
      self.assertEqual(result, "Unknown")
    finally:
      os.remove(config_path)

if __name__ == '__main__':
  unittest.main()
