import os
import json
from datetime import datetime
import requests

from .utils import WeatherUtils

class DarkSkyAPI:
  api_endpoint = "https://api.darksky.net/forecast"

  @property
  def name(self):
    return 'DarkSky'

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
    now['api_provider'] = self.name
    localtime = datetime.fromtimestamp(data['currently']['time'])
    now['time'] = localtime.strftime('%Y-%m-%d %H:%M:%S')
    now['temp'] = int(data['currently']['temperature'])
    now['high'] = int(data['daily']['data'][0]['temperatureHigh'])
    now['low'] = int(data['daily']['data'][0]['temperatureLow'])
    now['cond'] = data['currently']['icon']
    now['icon'] = now['cond']
    feels = int(data['currently']['apparentTemperature'])
    windSpeed = int(data['currently']['windSpeed'])
    windDir = WeatherUtils.get_direction(int(data['currently']['windBearing']))
    now['summary'] = f"{windSpeed} mph {windDir} wind, feels like {feels}°" 
    result['now'] = now

    hourly = list()
    for i in [1, 3, 5, 8, 11, 14]:
      forecast = data['hourly']['data'][i]
      localtime = datetime.fromtimestamp(forecast['time'])
      item = {}
      item['time'] = WeatherUtils.get_am_pm_hour_str(localtime)
      item['temp'] = int(forecast['temperature'])
      item['cond'] = forecast['icon']
      item['icon'] = item['cond']
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(1, 7):
      forecast = data['daily']['data'][i]
      localtime = datetime.fromtimestamp(forecast['time'])
      item = {}
      item['day'] = localtime.strftime('%a')
      item['date'] = localtime.strftime('%m/%d')
      item['high'] = int(forecast['temperatureHigh'])
      item['low'] =  int(forecast['temperatureLow'])
      item['cond'] = forecast['icon']
      item['icon'] = item['cond']
      daily.append(item)
    result['daily'] = daily
    return result

  def __api_call(self, lat, lon):
    API_URL = f"{DarkSkyAPI.api_endpoint}/{self.__api_key}/{lat},{lon}?units=us&lang=en"
    cache = WeatherUtils.load_api_dump(API_URL)
    if cache:
      return cache

    r = requests.get(API_URL)
    if r.status_code >= 400:
      raise Exception(f"REST API failed ({r.status_code}): {url}")

    WeatherUtils.save_api_dump(API_URL, r)
    return r.json()

  def forecast(self, lat, lon):
    api_result = self.__api_call(lat, lon)
    return self.__map_api_data(api_result)
