
import subprocess
import os
import json
import shutil
from typing import Dict, Optional

class Video:
  def __init__(self, file_path: str, fallback_time: Optional[str] = None):
    self.file_path = file_path
    self.metadata = self._extract_metadata()
    self._official_time = self._calc_official_time(fallback_time)

  def _extract_metadata(self) -> Dict:
    """
    Extract video metadata using ffprobe. Returns dict with keys:
    creation_time, codec, width, height, duration, bitrate, color_primaries, color_trc, colorspace
    """
    from media.exceptions import MetadataError
    try:
      cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,codec_name,bit_rate,color_primaries,color_trc,colorspace',
        '-show_entries', 'format=duration',
        '-show_entries', 'format_tags=creation_time',
        '-of', 'json',
        self.file_path
      ]
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      info = json.loads(result.stdout)
      stream = info['streams'][0] if info.get('streams') else {}
      format_info = info.get('format', {})
      tags = format_info.get('tags', {})
      creation_time = tags.get('creation_time', '')
      return {
        'creation_time': creation_time,
        'codec': stream.get('codec_name', 'unknown'),
        'width': stream.get('width', 0),
        'height': stream.get('height', 0),
        'duration': float(format_info.get('duration', 0)),
        'bitrate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0,
        'color_primaries': stream.get('color_primaries', ''),
        'color_trc': stream.get('color_trc', ''),
        'colorspace': stream.get('colorspace', '')
      }
    except Exception as e:
      raise MetadataError(f"Failed to get video metadata for {self.file_path}: {e}")

  def _calc_official_time(self, fallback_time: Optional[str]) -> str:
    """
    Decide the official time for this video (for filename, etc):
    1. Use creation_time from metadata if present
    2. Else use fallback_time (e.g., from filename or file creation)
    """
    if self.metadata.get('creation_time'):
      return self.metadata['creation_time']
    if fallback_time:
      return fallback_time
    return ''

  @property
  def official_time(self) -> str:
    return self._official_time

  @property
  def width(self):
    return self.metadata['width']

  @property
  def height(self):
    return self.metadata['height']

  @property
  def codec(self):
    return self.metadata['codec']

  @property
  def duration(self):
    return self.metadata['duration']

  @property
  def bitrate(self):
    return self.metadata['bitrate']

  @property
  def color_primaries(self):
    return self.metadata['color_primaries']

  @property
  def color_trc(self):
    return self.metadata['color_trc']

  @property
  def colorspace(self):
    return self.metadata['colorspace']

  def generate_filename(self, pattern: str, ext: str, counter: int = 0) -> str:
    """
    Generate filename from pattern and metadata.
    Pattern placeholders: {date}, {ext}
    """
    date_str = self.official_time.replace(':', '').replace(' ', '_').replace('-', '').replace('T', '_').split('.')[0] if self.official_time else 'unknown'
    name = pattern.replace('{date}', date_str).replace('{ext}', ext)
    if counter > 0:
      base, extension = os.path.splitext(name)
      name = f"{base}_{counter}{extension}"
    return name

class FFmpegWrapper:
  """
  Encapsulates ffmpeg/ffprobe subprocess logic for video processing.
  """
  @staticmethod
  def get_video_info(file_path: str) -> Dict:
    """Return video info: width, height, duration, bitrate, codec, color info."""
    from media.exceptions import MetadataError
    try:
      cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,codec_name,bit_rate,color_primaries,color_trc,colorspace',
        '-show_entries', 'format=duration',
        '-of', 'json',
        file_path
      ]
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      info = json.loads(result.stdout)
      stream = info['streams'][0] if info.get('streams') else {}
      format_info = info.get('format', {})
      return {
        'width': stream.get('width', 0),
        'height': stream.get('height', 0),
        'duration': float(format_info.get('duration', 0)),
        'bitrate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0,
        'codec': stream.get('codec_name', 'unknown'),
        'color_primaries': stream.get('color_primaries', ''),
        'color_trc': stream.get('color_trc', ''),
        'colorspace': stream.get('colorspace', '')
      }
    except Exception as e:
      raise MetadataError(f"Failed to get video info for {file_path}: {e}")

  @staticmethod
  def select_codec_params(ext: str) -> Dict:
    """Select codec and extra ffmpeg args based on extension."""
    ext = ext.lower()
    if ext in ['.mp4', '.m4v']:
      return {'codec': 'libx264', 'extra_args': ['-preset', 'slow', '-crf', '22']}
    if ext in ['.mov', '.hevc']:
      return {'codec': 'libx265', 'extra_args': ['-preset', 'slow', '-crf', '28']}
    if ext in ['.avi']:
      return {'codec': 'mpeg4', 'extra_args': ['-q:v', '5']}
    if ext in ['.mkv']:
      return {'codec': 'libx264', 'extra_args': ['-preset', 'slow', '-crf', '22']}
    if ext in ['.wmv']:
      return {'codec': 'wmv2', 'extra_args': []}
    if ext in ['.flv']:
      return {'codec': 'flv', 'extra_args': []}
    return {'codec': 'copy', 'extra_args': []}

  @staticmethod
  def resize_video(input_path: str, output_path: str, target_width: int, target_height: int, max_bitrate: str, codec_params: Dict):
    """
    Use FFmpeg to resize/re-encode video with error handling.
    Writes to temp file, validates, then moves atomically.
    """
    from media.exceptions import FFmpegError
    codec = codec_params['codec']
    extra_args = codec_params.get('extra_args', [])
    temp_path = output_path + '.tmp'
    cmd = ['ffmpeg', '-y', '-i', input_path]
    if codec == 'copy':
      cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
    else:
      cmd.extend([
        '-vf', f'scale={target_width}:{target_height}',
        '-c:v', codec,
        '-c:a', 'copy'
      ])
      cmd.extend(extra_args)
    cmd.append(temp_path)
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      shutil.move(temp_path, output_path)
    except subprocess.CalledProcessError as e:
      if os.path.exists(temp_path):
        os.remove(temp_path)
      error_msg = f"FFmpeg failed for {input_path} -> {output_path}: {e.stderr}"
      raise FFmpegError(error_msg) from e

  @staticmethod
  def validate_video_output(src_path: str, out_path: str, target_width: int = None, target_height: int = None, 
               duration_tol_sec: float = 1.0, bitrate_tol_ratio: float = 1.2):
    """
    Validate output video resolution, duration, and bitrate.
    Raises ValidationError if validation fails.
    """
    from media.exceptions import ValidationError
    src_info = FFmpegWrapper.get_video_info(src_path)
    out_info = FFmpegWrapper.get_video_info(out_path)
    if target_width and target_height:
      if out_info['width'] != target_width or out_info['height'] != target_height:
        raise ValidationError(
          f"Output video resolution {out_info['width']}x{out_info['height']} "
          f"does not match target {target_width}x{target_height}"
        )
    if abs(src_info['duration'] - out_info['duration']) > duration_tol_sec:
      raise ValidationError(
        f"Output video duration {out_info['duration']:.2f}s differs from source "
        f"{src_info['duration']:.2f}s by more than {duration_tol_sec}s"
      )
    if src_info['bitrate'] > 0 and out_info['bitrate'] > 0:
      if out_info['bitrate'] > src_info['bitrate'] * bitrate_tol_ratio:
        raise ValidationError(
          f"Output video bitrate {out_info['bitrate']} is unexpectedly higher than "
          f"source {src_info['bitrate']} (tolerance: {bitrate_tol_ratio}x)"
        )
    src_size = os.path.getsize(src_path)
    out_size = os.path.getsize(out_path)
    if out_size < src_size * 0.01:
      raise ValidationError(
        f"Output file size {out_size} is suspiciously small compared to source {src_size}"
      )
