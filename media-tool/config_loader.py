"""Configuration loader with schema validation, env substitution, path expansion."""

from __future__ import annotations

import os
import yaml
from typing import Any, Dict, List, Tuple, Union
from copy import deepcopy

from media.exceptions import ConfigError

_ENV_PREFIX = "${"
_ENV_SUFFIX = "}"

class ConfigLoader:
  """Advanced configuration loader.

  Features:
    - Dot-notation access (e.g. photo.max_width)
    - Schema validation (type, required, defaults)
    - Aggregated error reporting
    - Environment variable substitution (${VAR})
    - Path expansion (relative to config file and ~)
    - Reload capability
  """

  # key -> (expected_type(s), required, default)
  SCHEMA: Dict[str, Tuple[Union[type, Tuple[type, ...]], bool, Any]] = {
    "source_folder": (str, True, None),
    "staging_folder": (str, True, None),
    "log_file": (str, True, None),

    "photo.max_width": (int, True, None),
    "photo.max_height": (int, True, None),
    "photo.extensions": ((list, tuple), True, None),
    "photo.filename_pattern": (str, False, "{date}_{model}.{ext}"),

    "video.target_width": (int, True, None),
    "video.target_height": (int, True, None),
    "video.max_bitrate": (str, True, None),
    "video.extensions": ((list, tuple), True, None),
    "video.filename_pattern": (str, False, "{date}.{ext}"),
    "video.duration_tolerance_sec": (float, False, 1.0),
    "video.bitrate_tolerance_ratio": (float, False, 1.2),

    "duplicate_strategy": (str, False, "counter"),
    "ffmpeg_path": (str, False, None),
    "camera_model_mapping": (dict, False, {}),
  }

  def __init__(self, path: str, strict: bool = False):
    self.path = path
    self.strict = strict
    self._raw: Dict[str, Any] = {}
    self._config: Dict[str, Any] = {}
    self._load()
    self._validate()

  def _load(self) -> None:
    """Load YAML config file; error if missing."""
    if not os.path.exists(self.path):
      raise ConfigError(f"Config file not found: {self.path}")
    with open(self.path, "r", encoding="utf-8") as f:
      data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
      raise ConfigError("Top-level config must be a mapping object.")
    self._raw = data
    substituted = self._substitute_env(deepcopy(data))
    self._config = self._expand_paths(substituted)

  def reload(self) -> None:
    """Reload configuration from disk and re-validate."""
    self._load()
    self._validate()

  def get(self, key: str, default: Any = None) -> Any:
    parts = key.split('.')
    cur: Any = self._config
    for p in parts:
      if isinstance(cur, dict) and p in cur:
        cur = cur[p]
      else:
        return default
    return cur

  def all(self) -> Dict[str, Any]:
    return deepcopy(self._config)

  def _validate(self) -> None:
    errors: List[str] = []

    for key, (exp_type, required, default) in self.SCHEMA.items():
      val = self.get(key)
      if val is None:
        if required:
          errors.append(f"Missing required key: {key}")
        elif default is not None:
          self._assign(key, default)
        continue
      if not self._is_instance(val, exp_type):
        errors.append(
          f"Invalid type for '{key}': expected {self._type_name(exp_type)}, got {type(val).__name__}"
        )
      # Numeric validations
      if isinstance(val, (int, float)):
        if any(seg in key for seg in ("width", "height")) and val <= 0:
          errors.append(f"Value for '{key}' must be > 0")
        if "tolerance" in key and val < 0:
          errors.append(f"Value for '{key}' must be >= 0")

    # Strict mode: flag unknown top-level keys
    if self.strict:
      known_roots = {k.split('.')[0] for k in self.SCHEMA.keys()}
      for root_key in self._raw.keys():
        if root_key not in known_roots:
          errors.append(f"Unknown top-level key (strict mode): {root_key}")

    ffmpeg_path = self.get("ffmpeg_path")
    if ffmpeg_path:
      if not os.path.isfile(ffmpeg_path):
        errors.append(f"ffmpeg_path does not exist: {ffmpeg_path}")

    if errors:
      raise ConfigError("Configuration validation failed:\n" + "\n".join(errors))

  def list_missing(self) -> List[str]:
    return [k for k, (t, req, _) in self.SCHEMA.items() if req and self.get(k) is None]

  def _assign(self, key: str, value: Any) -> None:
    parts = key.split('.')
    target = self._config
    for p in parts[:-1]:
      if p not in target or not isinstance(target[p], dict):
        target[p] = {}
      target = target[p]
    target[parts[-1]] = value

  def _is_instance(self, value: Any, expected: Union[type, Tuple[type, ...]]) -> bool:
    if isinstance(expected, tuple):
      return isinstance(value, expected)
    return isinstance(value, expected)

  def _type_name(self, t: Union[type, Tuple[type, ...]]) -> str:
    if isinstance(t, tuple):
      return " or ".join(tt.__name__ for tt in t)
    return t.__name__

  def _substitute_env(self, obj: Any) -> Any:
    if isinstance(obj, dict):
      return {k: self._substitute_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
      return [self._substitute_env(v) for v in obj]
    if isinstance(obj, str):
      return self._replace_env_in_string(obj)
    return obj

  def _replace_env_in_string(self, s: str) -> str:
    out = s
    start = out.find(_ENV_PREFIX)
    while start != -1:
      end = out.find(_ENV_SUFFIX, start + len(_ENV_PREFIX))
      if end == -1:
        break
      var_name = out[start + len(_ENV_PREFIX):end]
      env_val = os.getenv(var_name, "")
      out = out[:start] + env_val + out[end + len(_ENV_SUFFIX):]
      start = out.find(_ENV_PREFIX, start + len(env_val))
    return out

  def _expand_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
    path_keys = ["source_folder", "staging_folder", "log_file", "ffmpeg_path"]
    base_dir = os.path.dirname(os.path.abspath(self.path))
    for pk in path_keys:
      raw = self._nested_get(config, pk)
      if isinstance(raw, str) and raw.strip():
        expanded = os.path.expanduser(raw)
        if not os.path.isabs(expanded):
          expanded = os.path.abspath(os.path.join(base_dir, expanded))
        self._assign(pk, expanded)
    return config

  def _nested_get(self, config: Dict[str, Any], key: str) -> Any:
    parts = key.split('.')
    cur: Any = config
    for p in parts:
      if isinstance(cur, dict):
        cur = cur.get(p)
      else:
        return None
    return cur
