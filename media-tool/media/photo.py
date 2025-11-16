
import pillow_heif
from PIL import Image
import piexif
import os
import shutil
from typing import Optional, Dict

pillow_heif.register_heif_opener()

class Photo:
  def __init__(self, file_path: str, fallback_time: Optional[str] = None):
    self.file_path = file_path
    self.img = Image.open(file_path)
    self.metadata = self._extract_metadata()
    self._official_time = self._calc_official_time(fallback_time)

  def _extract_metadata(self) -> Dict:
    meta = {'camera_model': '', 'taken_time': '', 'width': self.img.width, 'height': self.img.height}
    try:
      exif_data = self.img.info.get('exif')
      if exif_data:
        exif_dict = piexif.load(exif_data)
        model = exif_dict['0th'].get(piexif.ImageIFD.Model, b'').decode(errors='ignore').strip()
        dt = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal, b'').decode(errors='ignore').strip()
        meta['camera_model'] = model or 'Unknown'
        meta['taken_time'] = dt
      else:
        meta['camera_model'] = 'Unknown'
    except Exception:
      pass
    return meta

  def _calc_official_time(self, fallback_time: Optional[str]) -> str:
    """
    Decide the official time for this photo (for filename, etc):
    1. Use EXIF taken_time if present
    2. Else use fallback_time (e.g., from filename or file creation)
    """
    if self.metadata.get('taken_time'):
      return self.metadata['taken_time']
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
  def camera_model(self):
    return self.metadata['camera_model']

  def resize(self, output_path: str, max_width: int, max_height: int, quality: int) -> None:
    """
    Resize photo if needed, else copy. Writes atomically.
    """
    if self.img.width <= max_width and self.img.height <= max_height:
      shutil.copy2(self.file_path, output_path)
      return
    if self.img.format in ['HEIC', 'HEIF']:
      shutil.copy2(self.file_path, output_path)
      return
    exif_data = self.img.info.get('exif')
    img_copy = self.img.copy()
    img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    img_copy.save(output_path, quality=quality, exif=exif_data)

  def generate_filename(self, pattern: str, ext: str, counter: int = 0) -> str:
    """
    Generate filename from pattern and metadata.
    Pattern placeholders: {date}, {model}, {ext}
    """
    date_str = self.official_time.replace(':', '').replace(' ', '_') if self.official_time else 'unknown'
    model = self.camera_model.replace(' ', '')
    name = pattern.replace('{date}', date_str).replace('{model}', model).replace('{ext}', ext)
    if counter > 0:
      base, extension = os.path.splitext(name)
      name = f"{base}_{counter}{extension}"
    return name
