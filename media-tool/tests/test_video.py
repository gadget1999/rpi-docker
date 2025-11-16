"""Tests for video processing functions."""
import unittest
from media.video import Video, FFmpegWrapper


class TestVideoProcessing(unittest.TestCase):
    def test_generate_video_filename(self):
        video = Video(file_path='dummy.mp4')
        # Simulate metadata for test
        video._official_time = '2025-10-25T14:03:23.000Z'
        pattern = '{date}.{ext}'
        # Patch official_time property for test
        filename = video.generate_filename(pattern, 'mp4', counter=0)
        # The expected output should match the logic in generate_filename
        self.assertEqual(filename, '20251025_140323.mp4')

    def test_select_codec_params_copy(self):
        params = FFmpegWrapper.select_codec_params('.mp4')
        self.assertEqual(params['codec'], 'libx264')

    def test_select_codec_params_encode(self):
        params = FFmpegWrapper.select_codec_params('.mov')
        self.assertEqual(params['codec'], 'libx265')
        self.assertIn('-crf', params['extra_args'])

if __name__ == '__main__':
  unittest.main()
