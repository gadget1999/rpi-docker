"""Main entry point for the media tool."""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from config_loader import ConfigLoader
from logger import setup_logger, log_action
from media.base import analyze_file_type, extract_metadata
from media.photo import Photo
from media.video import Video, FFmpegWrapper
from media.exceptions import MediaProcessingError
from utils.file_ops import scan_folder_recursive, copy_file, handle_duplicates
from utils.date_utils import (
  parse_date_from_filename, get_file_modification_time, format_date_for_filename
)


def apply_camera_model_mapping(camera_model: str, config: ConfigLoader) -> str:
  """
  Apply camera model name mapping from config.
  Returns mapped name if found, otherwise returns original (stripped of whitespace).
  """
  if not camera_model:
    return ''
  
  # Get mapping from config
  mapping = config.get('camera_model_mapping', {})
  
  # Try exact match first
  if camera_model in mapping:
    return mapping[camera_model]
  
  # Try case-insensitive match
  camera_model_lower = camera_model.lower()
  for key, value in mapping.items():
    if key.lower() == camera_model_lower:
      return value
  
  # No mapping found, return original but clean it up
  # Remove extra spaces and special characters that could cause issues in filenames
  cleaned = camera_model.strip().replace(' ', '').replace('/', '_')
  return cleaned


def get_metadata_with_fallback(file_path: str, logger) -> dict:
  """
  Extract metadata with fallback chain:
  1. Try to extract from file metadata (EXIF, FFprobe)
  2. Try to parse from filename
  3. Fall back to file creation time
  """
  try:
    metadata = extract_metadata(file_path)
    
    # Check if we got a valid taken_time or creation_time
    taken_time = metadata.get('taken_time') or metadata.get('creation_time')
    
    if not taken_time:
      # Try parsing from filename
      filename = os.path.basename(file_path)
      parsed_date = parse_date_from_filename(filename)
      
      if parsed_date:
        taken_time = parsed_date.strftime('%Y:%m:%d %H:%M:%S')
        metadata['taken_time'] = taken_time
        log_action(logger, {
          'status': 'info',
          'file': file_path,
          'message': 'Date extracted from filename'
        })
      else:
        # Fall back to file creation time
        modification_time = get_file_modification_time(file_path)
        taken_time = modification_time.strftime('%Y:%m:%d %H:%M:%S')
        metadata['taken_time'] = taken_time
        log_action(logger, {
          'status': 'info',
          'file': file_path,
          'message': 'Using file modification time as fallback'
        })
    
    return metadata
  except Exception as e:
    log_action(logger, {
      'status': 'error',
      'file': file_path,
      'message': f'Metadata extraction failed: {e}'
    })
    # Return minimal metadata with creation time
    modification_time = get_file_modification_time(file_path)
    return {
      'type': analyze_file_type(file_path),
      'taken_time': modification_time.strftime('%Y:%m:%d %H:%M:%S'),
      'camera_model': 'Unknown'
    }


def process_photo(file_path: str, config: ConfigLoader, logger) -> dict:
  """Process a single photo file."""
  start_time = time.time()
  
  try:
    # Parse fallback time from filename or file modification
    fallback_time = None
    filename_date = parse_date_from_filename(os.path.basename(file_path))
    if filename_date:
      fallback_time = filename_date.strftime('%Y:%m:%d %H:%M:%S')
    else:
      fallback_time = get_file_modification_time(file_path).strftime('%Y:%m:%d %H:%M:%S')
    
    # Create Photo object
    photo = Photo(file_path, fallback_time=fallback_time)
    
    # Apply camera model mapping
    mapped_model = apply_camera_model_mapping(photo.camera_model, config)
    
    # Get config settings
    max_width = config.get('photo.max_width')
    max_height = config.get('photo.max_height')
    quality = config.get('photo.quality', 95)
    pattern = config.get('photo.filename_pattern', '{date}_{model}.{ext}')
    staging_folder = config.get('staging_folder')
    duplicate_strategy = config.get('duplicate_strategy', 'counter')
    
    # Parse date for folder structure
    taken_time_str = photo.metadata.get('taken_time', '')
    if taken_time_str:
      try:
        dt = datetime.strptime(taken_time_str, '%Y:%m:%d %H:%M:%S')
      except:
        dt = get_file_modification_time(file_path)
    else:
      dt = get_file_modification_time(file_path)
    
    # Generate new filename (update pattern to use mapped model)
    ext = os.path.splitext(file_path)[1].lstrip('.')
    if mapped_model.lower() == "unknown" or mapped_model == "":
      pattern_with_model = '{date}.{ext}'
    else:
      pattern_with_model = pattern.replace('{model}', mapped_model.replace(' ', ''))
    new_filename = photo.generate_filename(pattern_with_model, ext)
    
    # Build staging path with YYYY/YYYY.MM structure
    year_folder = dt.strftime('%Y')
    month_folder = dt.strftime('%Y.%m')
    staging_path = os.path.join(staging_folder, year_folder, month_folder, new_filename)
    
    # Handle duplicates
    final_path = handle_duplicates(staging_path, duplicate_strategy)
    if final_path is None:
      log_action(logger, {
        'status': 'skipped',
        'file': file_path,
        'reason': 'File already exists and duplicate_strategy is skip',
        'elapsed_ms': int((time.time() - start_time) * 1000)
      })
      return {'status': 'skipped', 'reason': 'duplicate'}
    
    # Create temp output path
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    
    # Resize photo using Photo object
    photo.resize(final_path, max_width, max_height, quality)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    log_action(logger, {
      'status': 'success',
      'type': 'photo',
      'source': file_path,
      'destination': final_path,
      'operations': ['resize', 'rename', 'copy'],
      'elapsed_ms': elapsed_ms
    })
    
    return {'status': 'success', 'path': final_path}
    
  except Exception as e:
    elapsed_ms = int((time.time() - start_time) * 1000)
    log_action(logger, {
      'status': 'error',
      'type': 'photo',
      'file': file_path,
      'error': str(e),
      'elapsed_ms': elapsed_ms
    })
    return {'status': 'error', 'error': str(e)}


def process_video(file_path: str, config: ConfigLoader, logger) -> dict:
  """Process a single video file."""
  start_time = time.time()
  
  try:
    # Parse fallback time from filename or file modification
    fallback_time = None
    filename_date = parse_date_from_filename(os.path.basename(file_path))
    if filename_date:
      fallback_time = filename_date.isoformat()
    else:
      fallback_time = get_file_modification_time(file_path).isoformat()
    
    # Create Video object
    video = Video(file_path, fallback_time=fallback_time)
    
    # Get config settings
    target_width = config.get('video.target_width')
    target_height = config.get('video.target_height')
    max_bitrate = config.get('video.max_bitrate')
    pattern = config.get('video.filename_pattern', '{date}.{ext}')
    staging_folder = config.get('staging_folder')
    duplicate_strategy = config.get('duplicate_strategy', 'counter')
    duration_tol = config.get('video.duration_tolerance_sec', 1.0)
    bitrate_tol = config.get('video.bitrate_tolerance_ratio', 1.2)
    
    # Parse date for folder structure
    creation_time_str = video.metadata.get('creation_time', '')
    if creation_time_str:
      try:
        # Handle ISO format: 2025-10-25T14:03:23.000Z
        if 'T' in creation_time_str:
          dt = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00').split('+')[0])
        else:
          dt = datetime.strptime(creation_time_str, '%Y:%m:%d %H:%M:%S')
      except:
        dt = get_file_modification_time(file_path)
    else:
      dt = get_file_modification_time(file_path)
    
    # Generate new filename
    ext = os.path.splitext(file_path)[1].lstrip('.')
    new_filename = video.generate_filename(pattern, ext)
    
    # Build staging path with YYYY/YYYY.MM structure
    year_folder = dt.strftime('%Y')
    month_folder = dt.strftime('%Y.%m')
    staging_path = os.path.join(staging_folder, year_folder, month_folder, new_filename)
    
    # Handle duplicates
    final_path = handle_duplicates(staging_path, duplicate_strategy)
    if final_path is None:
      log_action(logger, {
        'status': 'skipped',
        'file': file_path,
        'reason': 'File already exists and duplicate_strategy is skip',
        'elapsed_ms': int((time.time() - start_time) * 1000)
      })
      return {'status': 'skipped', 'reason': 'duplicate'}
    
    # Create output directory
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    
    # Select FFmpeg parameters
    file_ext = os.path.splitext(file_path)[1].lower()
    codec_params = FFmpegWrapper.select_codec_params(file_ext)
    
    # Resize/convert video using FFmpegWrapper
    FFmpegWrapper.resize_video(file_path, final_path, target_width, target_height, max_bitrate, codec_params)
    
    # Validate output using FFmpegWrapper
    FFmpegWrapper.validate_video_output(
      file_path,
      final_path,
      target_width,
      target_height,
      duration_tol,
      bitrate_tol
    )
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    operations = ['validate', 'rename', 'copy']
    if codec_params['codec'] != 'copy':
      operations.insert(0, 'resize')
      operations.insert(1, 'encode')
    
    log_action(logger, {
      'status': 'success',
      'type': 'video',
      'source': file_path,
      'destination': final_path,
      'codec': codec_params['codec'],
      'operations': operations,
      'elapsed_ms': elapsed_ms
    })
    
    return {'status': 'success', 'path': final_path}
    
  except Exception as e:
    elapsed_ms = int((time.time() - start_time) * 1000)
    log_action(logger, {
      'status': 'error',
      'type': 'video',
      'file': file_path,
      'error': str(e),
      'elapsed_ms': elapsed_ms
    })
    return {'status': 'error', 'error': str(e)}


def main():
  """Main orchestration function."""
  # Default config path
  config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
  
  # Allow config path override via command line
  if len(sys.argv) > 1:
    config_path = sys.argv[1]
  
  try:
    # Load configuration
    print(f"Loading configuration from: {config_path}")
    config = ConfigLoader(config_path)

    # Configure FFmpeg binaries if overridden in config
    FFmpegWrapper.configure(
      config.get('ffmpeg_path'),
      config.get('ffprobe_path')
    )
    
    # Setup logger
    log_file = config.get('log_file')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = setup_logger(log_file)
    
    # Get source folder and extensions
    source_folder = config.get('source_folder')
    photo_extensions = config.get('photo.extensions', [])
    video_extensions = config.get('video.extensions', [])
    all_extensions = photo_extensions + video_extensions
    
    print(f"Source folder: {source_folder}")
    print(f"Scanning for files with extensions: {all_extensions}")
    
    # Scan source folder
    files = scan_folder_recursive(source_folder, all_extensions)
    print(f"Found {len(files)} files to process")
    
    # Process each file
    results = {
      'total': len(files),
      'success': 0,
      'error': 0,
      'skipped': 0,
      'photos': 0,
      'videos': 0
    }
    
    for idx, file_path in enumerate(files, 1):
      print(f"\nProcessing [{idx}/{len(files)}]: {os.path.basename(file_path)}")
      
      file_type = analyze_file_type(file_path)
      
      if file_type == 'photo':
        result = process_photo(file_path, config, logger)
        results['photos'] += 1
      elif file_type == 'video':
        result = process_video(file_path, config, logger)
        results['videos'] += 1
      else:
        print(f"  Skipped: Unknown file type")
        results['skipped'] += 1
        continue
      
      if result['status'] == 'success':
        results['success'] += 1
        print(f"  ✓ Success: {result.get('path', 'N/A')}")
      elif result['status'] == 'error':
        results['error'] += 1
        print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
      elif result['status'] == 'skipped':
        results['skipped'] += 1
        print(f"  - Skipped: {result.get('reason', 'Unknown reason')}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Processing Complete")
    print("=" * 80)
    print(f"Total files:    {results['total']}")
    print(f"  Photos:       {results['photos']}")
    print(f"  Videos:       {results['videos']}")
    print(f"Successful:     {results['success']}")
    print(f"Errors:         {results['error']}")
    print(f"Skipped:        {results['skipped']}")
    print(f"\nLog file: {log_file}")
    
    logger.info(f"Processing Complete - Summary: {results}")
    
    return 0 if results['error'] == 0 else 1
    
  except Exception as e:
    print(f"\nFATAL ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    return 1


if __name__ == "__main__":
  sys.exit(main())
