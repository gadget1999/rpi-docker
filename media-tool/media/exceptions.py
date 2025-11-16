"""Custom exceptions for media processing."""

class MediaProcessingError(Exception):
  """Base exception for all media processing errors."""
  pass

class MetadataError(MediaProcessingError):
  """Raised when metadata extraction fails."""
  pass

class FFmpegError(MediaProcessingError):
  """Raised when FFmpeg execution fails."""
  pass

class ValidationError(MediaProcessingError):
  """Raised when output validation fails."""
  pass

class ConfigError(MediaProcessingError):
  """Raised when configuration is invalid."""
  pass
