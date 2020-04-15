import os
import json
import time
import re
import requests

import utils

ICON_PATH = "/static/images"
ICON_EXT = "png"

# detailed condition list: https://w1.weather.gov/xml/current_obs/weather.php (old)
# new mapping: https://saratoga-weather.org/advforecast2.php?sce=view
ICON_MAPPING = {
  "skc": "clear-day",
  "nskc": "clear-night",
  "few": "clear-day",
  "nfew": "clear-night",
  "sct": "partly-cloudy-day",
  "nsct": "partly-cloudy-night",
  "bkn": "cloudy",
  "wind_bkn": "cloudy",
  "ovc": "cloudy",
  "rain": "rain",
  "rain_showers": "rain",
  "rain_showers_hi": "rain",
  "tsra": "thunderstorm",
  "tsra_sct": "thunderstorm",
  "tsra_hi": "thunderstorm",
  "snow": "snow",
  "rain_snow": "snow",
  "snow_fzra": "snow",
  "snow_sleet": "sleet",
  "wind_bkn": "wind",
  "wind_few": "wind",
  "wind_ovc": "wind",
  "wind_sct": "wind",
  "wind_skc": "wind",
  "fg": "fog"
  }
NIGHT_ICONS = {
  "skc": "nskc",
  "few": "nfew",
  "sct": "nsct"
  }

def get_icon_path(icon_url):
  # icon example 1: https://api.weather.gov/icons/land/day/bkn?size=small
  # icon example 2: https://api.weather.gov/icons/land/night/rain_showers,30/rain_showers,50?size=medium
  icon_url = icon_url.replace('https://api.weather.gov/icons/land/', '')
  icon_url = icon_url.split('?')[0] # "day/bkn" or "night/rain_showers,30/rain_showers,50"
  icon = icon_url.split('/')[1] # "bkn" or "rain_showers,30"
  icon = icon.split(',')[0] # "bkn" or "rain_showers"
  # add night decoration to a few conditions
  if icon_url.startswith('night/'):
    icon = NIGHT_ICONS.get(icon, icon)
  standard_icon = ICON_MAPPING.get(icon, 'unknown')
  return f"{ICON_PATH}/{standard_icon}.{ICON_EXT}"

class NWSAPI:
  api_endpoint = "https://api.weather.gov/points"

  # NWS does not maintain daily high/low
  date = None
  daily_high = -200
  daily_low = 200

  def __init__(self, app_key):
    self.__headers = {'User-Agent': app_key}

  # map api return to standard format
  # data schema:
  # - now: time, temp, high, low, cond, icon, summary with feels, windSpeed, windDir
  # - hourly (every 1-3 hours, up to 6 items): time, temp, cond, icon
  # - daily (up to 6 days): day, date, high, low, cond, icon
  def __map_api_data(self, hourly_data, daily_data):
    result = {}

    # NWS half day series starts from current time until the 6:00/18:00 marks
    start_time = time.strptime(daily_data['properties']['periods'][0]['startTime'], "%Y-%m-%dT%H:%M:%S%z")
    current_temperature = int(hourly_data['properties']['periods'][0]['temperature'])
    if start_time.tm_hour > 18:
      # now is night, use current temperature as high and lowest as low
      tonight_index = 0
      daily_high = current_temperature
      daily_low = int(daily_data['properties']['periods'][tonight_index]['temperature'])
    elif start_time.tm_hour < 6:
      # now is early-morning, day is 6-18 (high) and night is after that (low)
      tonight_index = 2
      daily_high = int(daily_data['properties']['periods'][tonight_index-1]['temperature'])
      daily_low = int(daily_data['properties']['periods'][tonight_index]['temperature'])
    else:
      # day is now (high), night is next (low)
      tonight_index = 1
      daily_high = int(daily_data['properties']['periods'][tonight_index-1]['temperature'])
      daily_low = int(daily_data['properties']['periods'][tonight_index]['temperature'])

    # adjust for partial data (e.g., start time in the middle)
    if current_temperature > daily_high:
      daily_high = current_temperature
    if current_temperature < daily_low:
      daily_low = current_temperature

    # track daily high/low
    today = time.strftime('%Y-%m-%d', start_time)
    if today != NWSAPI.date:
      NWSAPI.date = today
      NWSAPI.daily_high = daily_high
      NWSAPI.daily_low = daily_low
    else:
      if NWSAPI.daily_high < daily_high:
        NWSAPI.daily_high = daily_high
      if NWSAPI.daily_low > daily_low:
        NWSAPI.daily_low = daily_low

    now = {}
    localtime = time.localtime()
    now['time'] = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    now['temp'] = current_temperature
    now['high'] = NWSAPI.daily_high
    now['low'] = NWSAPI.daily_low
    now['cond'] = hourly_data['properties']['periods'][0]['shortForecast']
    now['icon'] = get_icon_path(hourly_data['properties']['periods'][0]['icon'])
    now['summary'] = daily_data['properties']['periods'][0]['detailedForecast']
    result['now'] = now

    hourly = list()
    for i in [1, 3, 5, 8, 11, 14]:
      forecast_hour = hourly_data['properties']['periods'][i]
      localtime = time.strptime(forecast_hour['startTime'], "%Y-%m-%dT%H:%M:%S%z")
      item = {}
      item['time'] = utils.get_hour_str(localtime)
      item['temp'] = int(forecast_hour['temperature'])
      item['cond'] = forecast_hour['shortForecast']
      item['icon'] = get_icon_path(forecast_hour['icon'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(tonight_index+1, tonight_index+12, 2):
      if i > 12: # only 14 entries (max index is 13)
        continue
      forecast_day = daily_data['properties']['periods'][i]
      forecast_night = daily_data['properties']['periods'][i+1]
      localtime = time.strptime(forecast_day['startTime'], "%Y-%m-%dT%H:%M:%S%z")
      item = {}
      item['day'] = time.strftime('%a', localtime)
      item['date'] = time.strftime('%m/%d', localtime)
      item['high'] = int(forecast_day['temperature'])
      item['low'] =  int(forecast_night['temperature'])
      item['cond'] = forecast_day['shortForecast']
      item['icon'] = get_icon_path(forecast_day['icon'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, url):
    r = requests.get(url, headers=self.__headers)
    if r.status_code >= 400:
      raise Exception(f"REST API failed ({r.status_code}): {url}")
    return r.json()

  def __get_forecast_url(self, lat, lon):
    api_url = f"{NWSAPI.api_endpoint}/{lat},{lon}"
    station_info = self.__api_call(api_url)
    # half day forecast up to 7 days
    forecast_url = station_info['properties']['forecast']
    # hourly forecast up to 156 hours (6.5 days)
    hourly_url = station_info['properties']['forecastHourly']
    return forecast_url, hourly_url

  def forecast(self, lat, lon):
    forecast_url, hourly_url = self.__get_forecast_url(lat, lon)
    daily_result = self.__api_call(forecast_url)
    hourly_result = self.__api_call(hourly_url)
    return self.__map_api_data(hourly_result, daily_result)
