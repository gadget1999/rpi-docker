import os
from datetime import datetime
import requests

from .utils import WeatherUtils

# Mapping Tomorrow.io weatherCode to our icon names and a simple condition label
TOMORROW_ICON_MAP = {
  1000: ("Clear", "clear-day"),
  1100: ("Mostly Clear", "partly-cloudy-day"),
  1101: ("Partly Cloudy", "partly-cloudy-day"),
  1102: ("Mostly Cloudy", "cloudy"),
  1001: ("Cloudy", "cloudy"),
  2000: ("Fog", "fog"),
  2100: ("Light Fog", "fog"),
  4000: ("Drizzle", "rain"),
  4001: ("Rain", "rain"),
  4200: ("Light Rain", "rain"),
  4201: ("Heavy Rain", "rain"),
  5000: ("Snow", "snow"),
  5001: ("Flurries", "snow"),
  5100: ("Light Snow", "snow"),
  5101: ("Heavy Snow", "snow"),
  6000: ("Freezing Drizzle", "sleet"),
  6001: ("Freezing Rain", "sleet"),
  6200: ("Light Freezing Rain", "sleet"),
  6201: ("Heavy Freezing Rain", "sleet"),
  7000: ("Ice Pellets", "hail"),
  7101: ("Heavy Ice Pellets", "hail"),
  7102: ("Light Ice Pellets", "hail"),
  8000: ("Thunderstorm", "thunderstorm"),
}


class TomorrowAPI:
  realtime_endpoint = "https://api.tomorrow.io/v4/weather/realtime"
  forecast_endpoint = "https://api.tomorrow.io/v4/weather/forecast"

  @property
  def name(self):
    return 'Tomorrow.io'

  def __init__(self, app_key):
    self.__api_key = app_key

  def _map_icon(self, code: int):
    default = ("Unknown", "cloudy")
    return TOMORROW_ICON_MAP.get(code, default)

  def _parse_time(self, t: str):
    # Example: 2025-08-26T15:00:00Z
    try:
      if t.endswith('Z'):
        return datetime.fromisoformat(t.replace('Z', '+00:00')).astimezone()
      return datetime.fromisoformat(t)
    except Exception:
      # Fallback: return naive without tz
      return datetime.fromisoformat(t.replace('Z', ''))

  def _api_call(self, url):
    cache = WeatherUtils.load_api_dump(url)
    if cache:
      return cache

    r = requests.get(url)
    if r.status_code >= 400:
      raise Exception(f"REST API failed ({r.status_code}): {url}")

    WeatherUtils.save_api_dump(url, r)
    return r.json()

  def forecast(self, lat, lon):
    # Fetch realtime for 'now'
    realtime_url = f"{TomorrowAPI.realtime_endpoint}?location={lat},{lon}&units=imperial&apikey={self.__api_key}"
    realtime = self._api_call(realtime_url)

    # Fetch both hourly and daily forecasts
    forecast_url = f"{TomorrowAPI.forecast_endpoint}?location={lat},{lon}&timesteps=1h,1d&units=imperial&apikey={self.__api_key}"
    fc = self._api_call(forecast_url)

    result = {}

    # map now
    now_values = realtime.get('data', {}).get('values', {}) if 'data' in realtime else realtime.get('data', {})
    now_time = realtime.get('data', {}).get('time') if 'data' in realtime else realtime.get('time')
    now_dt = self._parse_time(now_time) if now_time else datetime.now()
    weather_code = int(now_values.get('weatherCode', 1001))
    cond, icon = self._map_icon(weather_code)
    temp = int(round(now_values.get('temperature', 0)))
    temp_app = int(round(now_values.get('temperatureApparent', temp)))
    wind_speed = int(round(now_values.get('windSpeed', 0)))
    wind_dir_deg = int(round(now_values.get('windDirection', 0)))
    wind_dir = WeatherUtils.get_direction(wind_dir_deg)
    humidity = int(round(now_values.get('humidity', 0)))

    now = {
      'api_provider': self.name,
      'time': now_dt.strftime('%Y-%m-%d %H:%M:%S'),
      'temp': temp,
      'high': 0,  # to be set from daily below
      'low': 0,   # to be set from daily below
      'cond': cond,
      'icon': icon,
      'summary': f"{wind_speed} mph {wind_dir} wind, feels like {temp_app}°, humidity {humidity}%",
    }

    # timelines for hourly/daily
    timelines = fc.get('timelines') or {}
    hourly_list = timelines.get('hourly') or []
    daily_list = timelines.get('daily') or []

    # get rain or snow chance and accumlation from hourly (add together)
    precipitation_chance = 0
    rain_accum = 0.0
    snow_accum = 0.0
    for h in hourly_list[:12]:  # next 12 hours for chance
      values = h.get('values', h) or {}
      precipitation_chance = max(precipitation_chance, int(round(values.get('precipitationProbability', 0))))
      rain_accum += float(values.get('rainAccumulation', 0.0))  # in inches
      snow_accum += float(values.get('snowAccumulation', 0.0)) # in inches
    if rain_accum > 0.0 or snow_accum > 0.0:
      if rain_accum > 0.0:
        now['summary'] += f", {rain_accum:.2f}\" rain"
      if snow_accum > 0.0:
        now['summary'] += f", {snow_accum:.2f}\" snow"
      if precipitation_chance > 0:
        now['summary'] += f" ({precipitation_chance}% chance)"

    # Map hourly: pick indices similar to others
    hourly = []
    pick = [1, 3, 5, 8, 11, 14]
    for i in pick:
      if i < len(hourly_list):
        h = hourly_list[i]
        t = h.get('time') or h.get('startTime')
        dt = self._parse_time(t)
        values = h.get('values', h)
        code = int(values.get('weatherCode', 1001))
        cond_h, icon_h = self._map_icon(code)
        item = {
          'time': WeatherUtils.get_am_pm_hour_str(dt),
          'temp': int(round(values.get('temperature', 0))),
          'cond': cond_h,
          'icon': icon_h,
        }
        hourly.append(item)
    result['hourly'] = hourly

    # Map daily: next 6 days
    daily = []
    for i in range(1, min(7, len(daily_list))):
      d = daily_list[i]
      t = d.get('time') or d.get('startTime')
      dt = self._parse_time(t)
      values = d.get('values', d)
      code = int(values.get('weatherCode', 1001))
      cond_d, icon_d = self._map_icon(code)
      item = {
        'day': dt.strftime('%a'),
        'date': dt.strftime('%m/%d'),
        'high': int(round(values.get('temperatureMax', values.get('temperature', 0)))),
        'low': int(round(values.get('temperatureMin', values.get('temperature', 0)))),
        'cond': cond_d,
        'icon': icon_d,
      }
      daily.append(item)
    result['daily'] = daily

    # Set today's high/low on now if available from first daily (index 0 in daily_list)
    if len(daily_list) > 0:
      values0 = daily_list[0].get('values', daily_list[0])
      now['high'] = int(round(values0.get('temperatureMax', now['temp'])))
      now['low'] = int(round(values0.get('temperatureMin', now['temp'])))

    result['now'] = now
    return result
