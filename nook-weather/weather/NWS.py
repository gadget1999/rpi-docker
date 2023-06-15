from datetime import datetime, timezone
from threading import RLock

import requests

from .utils import WeatherUtils

# detailed condition list: https://w1.weather.gov/xml/current_obs/weather.php (old)
# new mapping: https://saratoga-weather.org/advforecast2.php?sce=view
ICON_MAPPING = {
  "skc": "clear-day",
  "hot": "clear-day",
  "cold": "clear-day",
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
  "tropical_storm": "thunderstorm",
  "snow": "snow",
  "rain_snow": "snow",
  "snow_fzra": "snow",
  "fzra": "sleet",
  "rain_fzra": "sleet",
  "snow_sleet": "sleet",
  "wind_bkn": "wind",
  "wind_few": "wind",
  "wind_ovc": "wind",
  "wind_sct": "wind",
  "wind_skc": "wind",
  "haze": "fog",
  "smoke": "fog",
  "fog": "fog"
  }
NIGHT_ICONS = {
  "skc": "nskc",
  "few": "nfew",
  "sct": "nsct"
  }

# API has many timestamps, sometimes it's not current
#TAG_UPDATE_TIME = "updateTime"
TAG_UPDATE_TIME = "generatedAt"

class NWSAPIFactory:
  __app_key = None
  __lock = RLock()
  __workers = {}

  @property
  def name(self):
    return 'NWS'

  def __init__(self, app_key):
    self.__app_key = app_key

  def __get_worker(self, lat, lon):
    try:
      NWSAPIFactory.__lock.acquire()
      request_key = f"{lat},{lon}"
      if request_key not in NWSAPIFactory.__workers:
        worker = NWSAPI(self.__app_key)
        NWSAPIFactory.__workers[request_key] = worker
      return NWSAPIFactory.__workers[request_key]
    finally:
      NWSAPIFactory.__lock.release()    

  def forecast(self, lat, lon):
    worker = self.__get_worker(lat, lon)
    return worker.forecast(lat, lon)

class NWSAPI:
  __api_endpoint = "https://api.weather.gov/points"

  @property
  def name(self):
    return 'NWS'

  def __init__(self, app_key):
    self.__headers = {'User-Agent': app_key}
    # NWS does not maintain daily high/low
    self.date = None
    self.daily_high = -200
    self.daily_low = 200

  def __map_icon_name(icon_url):
    # icon example 1: https://api.weather.gov/icons/land/day/bkn?size=small
    # icon example 2: https://api.weather.gov/icons/land/night/rain_showers,30/rain_showers,50?size=medium
    icon_url = icon_url.replace('http://', 'https://')
    icon_url = icon_url.replace('https://api.weather.gov/icons/land/', '')
    icon_url = icon_url.split('?')[0] # "day/bkn" or "night/rain_showers,30/rain_showers,50"
    icon = icon_url.split('/')[1] # "bkn" or "rain_showers,30"
    icon = icon.split(',')[0] # "bkn" or "rain_showers"
    # add night decoration to a few conditions
    if icon_url.startswith('night/'):
      icon = NIGHT_ICONS.get(icon, icon)
    return ICON_MAPPING.get(icon, icon)

  # map api return to standard format
  # data schema:
  # - now: time, temp, high, low, cond, icon, summary with feels, windSpeed, windDir
  # - hourly (every 1-3 hours, up to 6 items): time, temp, cond, icon
  # - daily (up to 6 days): day, date, high, low, cond, icon
  def __map_api_data(self, hourly_data, daily_data):
    result = {}

    # Sometimes NWS will not return latest data, check freshness first
    report_times = []
    report_times.append(datetime.fromisoformat(daily_data['properties'][TAG_UPDATE_TIME]))
    report_times.append(datetime.fromisoformat(hourly_data['properties'][TAG_UPDATE_TIME]))
    report_time = min(report_times)

    current_time = datetime.now(timezone.utc)
    elapsed = (current_time - report_time).total_seconds()
    if (elapsed > 7200):
      raise Exception(f"API result is too old: {report_time.isoformat()}")

    # NWS half day series starts from current time until the 6:00/18:00 marks
    start_time = datetime.fromisoformat(daily_data['properties']['periods'][0]['startTime'])
    # assembly daily high/low
    current_temperature = int(hourly_data['properties']['periods'][0]['temperature'])
    if start_time.hour >= 18:
      # now is night, use current temperature as high and lowest as low
      tonight_index = 0
      daily_high = current_temperature
      daily_low = int(daily_data['properties']['periods'][tonight_index]['temperature'])
    elif start_time.hour < 6:
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
    today = start_time.strftime('%Y-%m-%d')
    if today != self.date:
      self.date = today
      self.daily_high = daily_high
      self.daily_low = daily_low
    else:
      if self.daily_high < daily_high:
        self.daily_high = daily_high
      if self.daily_low > daily_low:
        self.daily_low = daily_low

    now = {}
    localtime = datetime.fromisoformat(daily_data['properties'][TAG_UPDATE_TIME]).astimezone()
    now['api_provider'] = self.name
    now['time'] = localtime.strftime('%Y-%m-%d %H:%M:%S')
    now['temp'] = current_temperature
    now['high'] = self.daily_high
    now['low'] = self.daily_low
    now['cond'] = hourly_data['properties']['periods'][0]['shortForecast']
    now['icon'] = NWSAPI.__map_icon_name(hourly_data['properties']['periods'][0]['icon'])
    now['summary'] = daily_data['properties']['periods'][0]['detailedForecast']
    result['now'] = now

    hourly = list()
    for i in [1, 3, 5, 8, 11, 14]:
      forecast_hour = hourly_data['properties']['periods'][i]
      localtime = datetime.fromisoformat(forecast_hour['startTime']).astimezone()
      item = {}
      item['time'] = WeatherUtils.get_am_pm_hour_str(localtime)
      item['temp'] = int(forecast_hour['temperature'])
      item['cond'] = forecast_hour['shortForecast']
      item['icon'] = NWSAPI.__map_icon_name(forecast_hour['icon'])
      hourly.append(item)
    result['hourly'] = hourly

    daily = list()
    for i in range(tonight_index+1, tonight_index+12, 2):
      if i > 12: # only 14 entries (max index is 13)
        continue
      forecast_day = daily_data['properties']['periods'][i]
      forecast_night = daily_data['properties']['periods'][i+1]
      localtime = datetime.fromisoformat(forecast_day['startTime'])
      item = {}
      item['day'] = localtime.strftime('%a')
      item['date'] = localtime.strftime('%m/%d')
      item['high'] = int(forecast_day['temperature'])
      item['low'] =  int(forecast_night['temperature'])
      item['cond'] = forecast_day['shortForecast']
      item['icon'] = NWSAPI.__map_icon_name(forecast_day['icon'])
      daily.append(item)
    result['daily'] = daily

    return result

  def __api_call(self, url):
    cache = WeatherUtils.load_api_dump(url)
    if cache:
      return cache

    r = requests.get(url, headers=self.__headers)
    if r.status_code >= 400:
      raise Exception(f"REST API failed ({r.status_code}): {url}")

    WeatherUtils.save_api_dump(url, r)
    return r.json()

  def __get_forecast_url(self, lat, lon):
    api_url = f"{NWSAPI.__api_endpoint}/{lat},{lon}"
    station_info = self.__api_call(api_url)
    # half day forecast up to 7 days
    forecast_url = station_info['properties']['forecast']
    # hourly forecast up to 156 hours (6.5 days)
    hourly_url = station_info['properties']['forecastHourly']
    return forecast_url, hourly_url

  def forecast(self, lat, lon):
    forecast_url, hourly_url = self.__get_forecast_url(lat, lon)
    forecast_url += "?units=us"  # seems a bug in API that always get old data without this
    daily_result = self.__api_call(forecast_url)
    hourly_result = self.__api_call(hourly_url)
    return self.__map_api_data(hourly_result, daily_result)
