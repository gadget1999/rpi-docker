#!/usr/bin/env python

import os
import sys
import json
import time
import requests

def compass(bearing):
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

ICON_PATH = "/static/images"
ICON_EXT = "png"
def get_icon_path(cond):
  return f"{ICON_PATH}/{cond}.{ICON_EXT}"

DARKSKY_API_ENDPOINT = "https://api.darksky.net/forecast"
class DarkSkyAPI:
  _api_key = None

  def __init__(self, app_key):
    self._api_key = app_key

  # map api return to standard format
  # data schema:
  # - now: time, temp, high, low, feel, cond, icon, windSpeed, windDir
  # - hourly (every 3 hours, up to 6 items): time, temp, cond, icon
  # - daily (up to 5 days): day, date, high, low, cond, icon
  def __map_api_data(self, data):
    result = {}

    now = {}
    unixtime = time.localtime(data['currently']['time'])
    now['time'] = time.strftime('%Y-%m-%d %H:%M:%S', unixtime)
    now['temp'] =  int(data['currently']['temperature'])
    now['feel'] =  int(data['currently']['apparentTemperature'])
    now['high'] = int(data['daily']['data'][0]['temperatureHigh'])
    now['low'] =  int(data['daily']['data'][0]['temperatureLow'])
    now['cond'] = data['currently']['icon']
    now['icon'] = get_icon_path(now['cond'])
    now['windSpeed'] = int(data['currently']['windSpeed'])
    now['windDir'] = compass(int(data['currently']['windBearing']))
    result['now'] = now

    hourly = list()
    for i in [3, 6, 9, 12, 15, 18]:
      forecast = data['hourly']['data'][i]
      unixtime = time.localtime(forecast['time'])
      item = {}
      item['time'] = time.strftime('%I %p', unixtime)
      item['temp'] = int(forecast['temperature'])
      item['cond'] = forecast['icon']
      item['icon'] = get_icon_path(item['cond'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(1, 7):
      forecast = data['daily']['data'][i]
      unixtime = time.localtime(forecast['time'])
      item = {}
      item['day'] = time.strftime('%a', unixtime)
      item['date'] = time.strftime('%m/%d', unixtime)
      item['high'] = int(forecast['temperatureHigh'])
      item['low'] =  int(forecast['temperatureLow'])
      item['cond'] = forecast['icon']
      item['icon'] = get_icon_path(item['cond'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, lat, lon):
    debug_json = os.environ.get('DEBUG_JSON', None)
    if debug_json and os.path.exists(debug_json):
      with open(debug_json) as r:
        return json.load(r)

    API_URL = f"{DARKSKY_API_ENDPOINT}/{self._api_key}/{lat},{lon}?units=us&lang=en"
    r = requests.get(API_URL)

    if debug_json:
      with open(debug_json, "w") as w:
        w.write(r.text)

    return(r.json())

  def forecast(self, lat, lon):
    api_result = self.__api_call(lat, lon)
    return self.__map_api_data(api_result)