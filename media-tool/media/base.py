from typing import Optional, Dict
import os

def analyze_file_type(file_path: str) -> Optional[str]:
  """Determine if file is photo or video based on extension."""
  ext = os.path.splitext(file_path)[1].lower()
  if ext in ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp', '.tiff']:
    return 'photo'
  if ext in ['.mp4', '.mov', '.hevc', '.avi', '.mkv', '.m4v', '.wmv', '.flv']:
    return 'video'
  return None

def extract_metadata(file_path: str) -> Dict:
  """
  Extract metadata from media file.
  Delegates to photo or video specific extractors.
  Returns dict with common fields: type, camera_model, taken_time, width, height.
  """
  file_type = analyze_file_type(file_path)
  
  if file_type == 'photo':
    from media.photo import Photo
    photo = Photo(file_path)
    metadata = photo.metadata.copy()
    metadata['type'] = 'photo'
    return metadata
  elif file_type == 'video':
    from media.video import Video
    video = Video(file_path)
    metadata = video.metadata.copy()
    metadata['type'] = 'video'
    return metadata
  return {'type': 'unknown'}
