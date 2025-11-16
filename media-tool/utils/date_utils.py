import os
import re
import platform
from datetime import datetime
from typing import Optional

def parse_date_from_filename(filename: str) -> Optional[datetime]:
  """Try to extract date from filename using common patterns."""
  # Pattern 1: YYYYMMDD_HHMMSS
  match = re.search(r'(\d{8})_(\d{6})', filename)
  if match:
    try:
      return datetime.strptime(match.group(1) + match.group(2), '%Y%m%d%H%M%S')
    except Exception:
      pass
  
  # Pattern 2: YYYY-MM-DD_HH-MM-SS
  match = re.search(r'(\d{4})-(\d{2})-(\d{2})[_\s](\d{2})-(\d{2})-(\d{2})', filename)
  if match:
    try:
      return datetime.strptime(f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}{match.group(5)}{match.group(6)}", '%Y%m%d%H%M%S')
    except Exception:
      pass
  
  # Pattern 3: Unix timestamp (10 digits)
  match = re.search(r'(\d{10})', filename)
  if match:
    try:
      return datetime.fromtimestamp(int(match.group(1)))
    except Exception:
      pass
  
  return None

def get_file_modification_time(file_path: str) -> datetime:
  """
  Get file modify time in a cross-platform way.
  """
  stat_info = os.stat(file_path)
  return datetime.fromtimestamp(stat_info.st_mtime)

def format_date_for_filename(dt: datetime, pattern: str = None) -> str:
  """
  Format datetime for filename.
  Default pattern produces: YYYYMMDD_HHMMSS
  """
  if pattern:
    # Support custom patterns: {date} gets replaced with YYYYMMDD_HHMMSS
    return dt.strftime('%Y%m%d_%H%M%S')
  return dt.strftime('%Y%m%d_%H%M%S')
