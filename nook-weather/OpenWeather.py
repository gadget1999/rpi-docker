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
COND_MAPPING = {
    "thunderstorm" : "thunderstorm",
    "drizzle" : "rain",
    "sleet" : "sleet",
    "rain" : "rain",
    "snow" : "snow",
    "mist" : "fog",
    "fog" : "fog",
    "clear" : "clear-day",
    "clouds" : "cloudy"
    }
def get_icon_path(cond):
  cond = cond.lower()
  if cond in COND_MAPPING:
    icon = COND_MAPPING[cond]
    return f"{ICON_PATH}/{icon}.{ICON_EXT}"

  # return non-existing icon to show ALT text
  return f"{ICON_PATH}/unknown.{ICON_EXT}"

OPEN_WEATHER_API_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall"
class OpenWeatherAPI:
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
    unixtime = time.localtime(data['current']['dt'])
    now['time'] = time.strftime('%Y-%m-%d %H:%M:%S', unixtime)
    now['temp'] =  int(data['current']['temp'])
    now['feel'] =  int(data['current']['feels_like'])
    now['high'] = int(data['daily'][0]['temp']['max'])
    now['low'] =  int(data['daily'][0]['temp']['min'])
    now['cond'] = data['current']['weather'][0]['main']
    now['icon'] = get_icon_path(now['cond'])
    now['windSpeed'] = int(data['current']['wind_speed'])
    now['windDir'] = compass(int(data['current']['wind_deg']))
    result['now'] = now

    hourly = list()
    for i in [3, 6, 9, 12, 15, 18]:
      forecast = data['hourly'][i]
      unixtime = time.localtime(forecast['dt'])
      item = {}
      item['time'] = time.strftime('%I %p', unixtime)
      item['temp'] = int(forecast['temp'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = get_icon_path(item['cond'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(1, 7):
      forecast = data['daily'][i]
      unixtime = time.localtime(forecast['dt'])
      item = {}
      item['day'] = time.strftime('%a', unixtime)
      item['date'] = time.strftime('%m/%d', unixtime)
      item['high'] = int(forecast['temp']['max'])
      item['low'] =  int(forecast['temp']['min'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = get_icon_path(item['cond'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, lat, lon):
    debug_json = os.environ.get('DEBUG_JSON', None)
    if debug_json and os.path.exists(debug_json):
      with open(debug_json) as r:
        return json.load(r)

    API_URL = f"{OPEN_WEATHER_API_ENDPOINT}?lat={lat}&lon={lon}&appid={self._api_key}&units=imperial&lang=en"
    r = requests.get(API_URL)

    if debug_json:
      with open(debug_json, "w") as w:
        w.write(r.text)

    return(r.json())

  def forecast(self, lat, lon):
    api_result = self.__api_call(lat, lon)
    return self.__map_api_data(api_result)
