"""Tests for enhanced ConfigLoader."""
import unittest
import tempfile
import os
from config_loader import ConfigLoader
from media.exceptions import ConfigError

VALID_BASE = """
source_folder: ./src
staging_folder: ./stage
log_file: ./logs/app.log
photo:
  max_width: 3840
  max_height: 2160
  extensions: [".jpg", ".png"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
"""

class TestConfigLoader(unittest.TestCase):
  def _write_temp_config(self, content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    f.write(content)
    f.flush()
    f.close()
    return f.name

  def test_load_valid_config(self):
    path = self._write_temp_config(VALID_BASE)
    try:
      cfg = ConfigLoader(path)
      # Paths should be expanded to absolute
      self.assertTrue(os.path.isabs(cfg.get('source_folder')))
      self.assertEqual(cfg.get('photo.max_width'), 3840)
      self.assertEqual(cfg.get('video.target_width'), 1920)
      # Defaults applied
      self.assertEqual(cfg.get('video.duration_tolerance_sec'), 1.0)
      self.assertEqual(cfg.get('duplicate_strategy'), 'counter')
    finally:
      os.remove(path)

  def test_missing_multiple_keys_aggregated(self):
    incomplete = """
source_folder: ./src
photo:
  max_width: 3840
"""
    path = self._write_temp_config(incomplete)
    try:
      with self.assertRaises(ConfigError) as ctx:
        ConfigLoader(path)
      msg = str(ctx.exception)
      self.assertIn('Missing required key: staging_folder', msg)
      self.assertIn('Missing required key: log_file', msg)
      self.assertIn('Missing required key: photo.max_height', msg)
      self.assertIn('Missing required key: photo.extensions', msg)
      self.assertIn('Missing required key: video.target_width', msg)
    finally:
      os.remove(path)

  def test_type_validation(self):
    bad_types = """
source_folder: ./src
staging_folder: ./stage
log_file: ./logs/app.log
photo:
  max_width: "wide"
  max_height: 2160
  extensions: [".jpg"]
video:
  target_width: 1920
  target_height: 1080
  max_bitrate: "8M"
  extensions: [".mp4"]
"""
    path = self._write_temp_config(bad_types)
    try:
      with self.assertRaises(ConfigError) as ctx:
        ConfigLoader(path)
      self.assertIn("Invalid type for 'photo.max_width'", str(ctx.exception))
    finally:
      os.remove(path)

  def test_env_substitution(self):
    os.environ['TEST_SOURCE'] = '/env/source'
    content = """
source_folder: "${TEST_SOURCE}"
staging_folder: ./stage
log_file: ./log.txt
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
    path = self._write_temp_config(content)
    try:
      cfg = ConfigLoader(path)
      self.assertEqual(os.path.normpath(cfg.get('source_folder')), os.path.normpath('/env/source'))
    finally:
      os.remove(path)

  def test_reload(self):
    path = self._write_temp_config(VALID_BASE)
    try:
      cfg = ConfigLoader(path)
      # Modify on disk
      with open(path, 'a', encoding='utf-8') as f:
        f.write('\nvideo:\n  target_width: 1280\n  target_height: 720\n  max_bitrate: "4M"\n  extensions: [".mp4"]')
      cfg.reload()
      self.assertEqual(cfg.get('video.target_width'), 1280)
    finally:
      os.remove(path)

if __name__ == '__main__':
  unittest.main()
