import os
import json
import time
import requests

import utils

ICON_PATH = "/static/images"
ICON_EXT = "png"

# detailed condition list: https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
ICON_MAPPING = {
  "01d": "clear-day",
  "01n": "clear-night",
  "02d": "partly-cloudy-day",
  "02n": "partly-cloudy-night",
  "03d": "cloudy",
  "03n": "cloudy",
  "04d": "cloudy",
  "04n": "cloudy",
  "09d": "rain",
  "09n": "rain",
  "10d": "rain",
  "10n": "rain",
  "11d": "thunderstorm",
  "11n": "thunderstorm",
  "13d": "snow",
  "13n": "snow",
  "50d": "fog",
  "50n": "fog"
  }

def get_icon_path(icon):
  standard_icon = ICON_MAPPING.get(icon, 'unknown')
  return f"{ICON_PATH}/{standard_icon}.{ICON_EXT}"

class OpenWeatherAPI:
  api_endpoint = "https://api.openweathermap.org/data/2.5/onecall"

  def __init__(self, app_key):
    self.__api_key = app_key

  # map api return to standard format
  # data schema:
  # - now: time, temp, high, low, cond, icon, summary with feels, windSpeed, windDir
  # - hourly (every 1-3 hours, up to 6 items): time, temp, cond, icon
  # - daily (up to 6 days): day, date, high, low, cond, icon
  def __map_api_data(self, data):
    result = {}

    now = {}
    localtime = time.localtime(data['current']['dt'])
    now['time'] = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    now['temp'] = int(data['current']['temp'])
    now['high'] = int(data['daily'][0]['temp']['max'])
    now['low'] = int(data['daily'][0]['temp']['min'])
    now['cond'] = data['current']['weather'][0]['main']
    now['icon'] = get_icon_path(data['current']['weather'][0]['icon'])
    feels = int(data['current']['feels_like'])
    windSpeed = int(data['current']['wind_speed'])
    windDir = utils.get_direction(int(data['current']['wind_deg']))
    now['summary'] = f"{windSpeed} mph {windDir} wind, feels like {feels}°" 
    result['now'] = now

    hourly = list()
    for i in [1, 3, 5, 8, 11, 14]:
      forecast = data['hourly'][i]
      localtime = time.localtime(forecast['dt'])
      item = {}
      item['time'] = utils.get_hour_str(localtime)
      item['temp'] = int(forecast['temp'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = get_icon_path(forecast['weather'][0]['icon'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(1, 7):
      forecast = data['daily'][i]
      localtime = time.localtime(forecast['dt'])
      item = {}
      item['day'] = time.strftime('%a', localtime)
      item['date'] = time.strftime('%m/%d', localtime)
      item['high'] = int(forecast['temp']['max'])
      item['low'] =  int(forecast['temp']['min'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = get_icon_path(forecast['weather'][0]['icon'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, lat, lon):
    debug_json = os.environ.get('DEBUG', None)
    if debug_json and os.path.exists(debug_json):
      with open(debug_json) as r:
        return json.load(r)

    API_URL = f"{OpenWeatherAPI.api_endpoint}?lat={lat}&lon={lon}&appid={self.__api_key}&units=imperial&lang=en"
    r = requests.get(API_URL)

    if debug_json:
      with open(debug_json, "w") as w:
        w.write(r.text)

    return(r.json())

  def forecast(self, lat, lon):
    api_result = self.__api_call(lat, lon)
    return self.__map_api_data(api_result)
