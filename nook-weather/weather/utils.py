import os
import json
import platform
import datetime
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

  def get_am_pm_hour_str(timestamp):
    if platform.system() == 'Windows':
      return timestamp.strftime('%#I %p')
    else:
      return timestamp.strftime('%-I %p')

  def load_api_dump(url):
    if 'DEBUG' in os.environ:
      hash = binascii.crc32(url.encode('utf8'))
      debug_json = f"/tmp/{hash}.json"
      if os.path.exists(debug_json):
        with open(debug_json) as r:
          return json.load(r)

  def save_api_dump(url, r):
    if 'DEBUG' in os.environ or os.path.exists('/tmp/dump-api.flag'):
      hash = binascii.crc32(url.encode('utf8'))
      debug_json = f"/tmp/{hash}.json"
      with open(debug_json, "w") as w:
        w.write(f"URL: {url}\r\n")
        w.write(r.text)
