import os
import json
from datetime import datetime
import requests

from .utils import WeatherUtils

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

class OpenWeatherAPI:
  api_endpoint = "https://api.openweathermap.org/data/2.5/onecall"

  @property
  def name(self):
    return 'OpenWeather'

  def __init__(self, app_key):
    self.__api_key = app_key

  def __map_icon_name(icon):
    return ICON_MAPPING.get(icon, 'unknown')

  # map api return to standard format
  # data schema:
  # - now: time, temp, high, low, cond, icon, summary with feels, windSpeed, windDir
  # - hourly (every 1-3 hours, up to 6 items): time, temp, cond, icon
  # - daily (up to 6 days): day, date, high, low, cond, icon
  def __map_api_data(self, data):
    result = {}

    now = {}
    now['api_provider'] = self.name
    localtime = datetime.fromtimestamp(data['current']['dt'])
    now['time'] = localtime.strftime('%Y-%m-%d %H:%M:%S')
    now['temp'] = int(data['current']['temp'])
    now['high'] = int(data['daily'][0]['temp']['max'])
    now['low'] = int(data['daily'][0]['temp']['min'])
    now['cond'] = data['current']['weather'][0]['main']
    now['icon'] = OpenWeatherAPI.__map_icon_name(data['current']['weather'][0]['icon'])
    feels = int(data['current']['feels_like'])
    windSpeed = int(data['current']['wind_speed'])
    windDir = WeatherUtils.get_direction(int(data['current']['wind_deg']))
    now['summary'] = f"{windSpeed} mph {windDir} wind, feels like {feels}°" 
    result['now'] = now

    hourly = list()
    for i in [1, 3, 5, 8, 11, 14]:
      forecast = data['hourly'][i]
      localtime = datetime.fromtimestamp(forecast['dt'])
      item = {}
      item['time'] = WeatherUtils.get_am_pm_hour_str(localtime)
      item['temp'] = int(forecast['temp'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = OpenWeatherAPI.__map_icon_name(forecast['weather'][0]['icon'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(1, 7):
      forecast = data['daily'][i]
      localtime = datetime.fromtimestamp(forecast['dt'])
      item = {}
      item['day'] = localtime.strftime('%a')
      item['date'] = localtime.strftime('%m/%d')
      item['high'] = int(forecast['temp']['max'])
      item['low'] =  int(forecast['temp']['min'])
      item['cond'] = forecast['weather'][0]['main']
      item['icon'] = OpenWeatherAPI.__map_icon_name(forecast['weather'][0]['icon'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, lat, lon):
    API_URL = f"{OpenWeatherAPI.api_endpoint}?lat={lat}&lon={lon}&appid={self.__api_key}&units=imperial&lang=en"
    cache = WeatherUtils.load_api_dump(API_URL)
    if cache:
      return cache

    r = requests.get(API_URL)
    if r.status_code >= 400:
      raise Exception(f"REST API failed ({r.status_code}): {url}")

    WeatherUtils.save_api_dump(API_URL, r)
    return(r.json())

  def forecast(self, lat, lon):
    api_result = self.__api_call(lat, lon)
    return self.__map_api_data(api_result)
