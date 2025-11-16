import os
from typing import List, Optional
import shutil

def scan_folder_recursive(folder: str, extensions: List[str]) -> List[str]:
  """Scan folder recursively for files matching extensions."""
  matches = []
  for root, _, files in os.walk(folder):
    for f in files:
      if any(f.lower().endswith(ext.lower()) for ext in extensions):
        matches.append(os.path.join(root, f))
  return matches

def copy_file(src: str, dst: str):
  """Copy file, creating parent directories as needed."""
  os.makedirs(os.path.dirname(dst), exist_ok=True)
  shutil.copy2(src, dst)

def handle_duplicates(dst_path: str, strategy: str = 'counter') -> Optional[str]:
  """
  Handle duplicate files based on strategy.
  
  Args:
    dst_path: Destination file path
    strategy: 'counter' (append _1, _2, etc.) or 'skip' (return None)
  
  Returns:
    Available path or None if strategy is 'skip' and file exists
  """
  if not os.path.exists(dst_path):
    return dst_path
  
  if strategy == 'skip':
    return None
  
  # Counter strategy
  base, ext = os.path.splitext(dst_path)
  counter = 1
  new_path = dst_path
  while os.path.exists(new_path):
    new_path = f"{base}_{counter}{ext}"
    counter += 1
  return new_path
