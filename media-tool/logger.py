import logging
from typing import Dict
import json

def setup_logger(log_path: str) -> logging.Logger:
  logger = logging.getLogger("media_tool")
  logger.setLevel(logging.INFO)
  
  # File handler
  fh = logging.FileHandler(log_path, encoding='utf-8')
  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
  fh.setFormatter(formatter)
  
  # Console handler
  ch = logging.StreamHandler()
  ch.setFormatter(formatter)
  
  if not logger.hasHandlers():
    logger.addHandler(fh)
    logger.addHandler(ch)
  
  return logger

def log_action(logger: logging.Logger, info: Dict):
  """Log structured action information."""
  # Convert dict to JSON string for structured logging
  log_msg = json.dumps(info, ensure_ascii=False)
  
  status = info.get('status', 'unknown')
  if status == 'success':
    logger.info(log_msg)
  elif status == 'error':
    logger.error(log_msg)
  else:
    logger.warning(log_msg)
