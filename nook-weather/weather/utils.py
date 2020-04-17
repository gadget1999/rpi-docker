import os
import json
import platform
import time
import binascii

class WeatherUtils:
  def get_direction(bearing):
    coords = {
      'N':  [0, 22.5],
      'NE': [22.5, 67.5],
      'E':  [67.5, 112.5],
      'SE': [112.5, 157.5],
      'S':  [157.5, 202.5],
      'SW': [202.5, 247.5],
      'W':  [247.5, 292.5],
      'NW': [292.5, 337.5],
      'N':  [337.5, 360]
    }
    for k,v in coords.items():
      if bearing >= v[0] and bearing < v[1]:
        return k

  def get_hour_str(timestamp):
    if platform.system() == 'Windows':
      return time.strftime('%#I %p', timestamp)
    else:
      return time.strftime('%-I %p', timestamp)

  def parse_ISO8601_time(time_str):
    return time.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")

  def ISO8601_2_local(time_str):
    t = WeatherUtils.parse_ISO8601_time(time_str)
    if t.tm_gmtoff != 0:
      return t

    tmp_localtime = time.localtime()
    localtime = time.mktime(t) + tmp_localtime.tm_gmtoff
    return time.localtime(localtime)

  def load_api_dump(url):
    if 'DEBUG' in os.environ:
      hash = binascii.crc32(url.encode('utf8'))
      debug_json = f"/tmp/{hash}.json"
      if os.path.exists(debug_json):
        with open(debug_json) as r:
          return json.load(r)

  def save_api_dump(url, r):
    if 'DEBUG' in os.environ:
      hash = binascii.crc32(url.encode('utf8'))
      debug_json = f"/tmp/{hash}.json"
      with open(debug_json, "w") as w:
        w.write(r.text)
