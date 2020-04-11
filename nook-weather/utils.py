import platform
import time

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