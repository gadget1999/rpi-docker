#!/usr/bin/env python

import os
import time
from threading import RLock

from .DarkSky import DarkSkyAPI
from .OpenWeather import OpenWeatherAPI
from .NWS import NWSAPI

import logging
logger = logging.getLogger()

class WeatherForecast:
  __api_providers = []
  __lock = RLock()
  __last_request_time = time.localtime(0)
  __last_forecast_data = None

  def init_from_env():
    # get list of API providers (in case one fails)
    for i in range(1, 5, 1):
      if not f"WEATHER_API_PROVIDER_{i}" in os.environ:
        break
  
      name = os.environ[f"WEATHER_API_PROVIDER_{i}"]
      key = os.environ[f"WEATHER_API_KEY_{i}"]
      if name.lower() == "nws":
        api_provider = NWSAPI(key)
      elif name.lower() == "darksky":
        api_provider = DarkSkyAPI(key)
      elif name.lower() == "openweather":
        api_provider = OpenWeatherAPI(key)
      else:
        raise Exception(f"Unknown weather API provider: {name}")

      WeatherForecast.__api_providers.append(api_provider)

    if not WeatherForecast.__api_providers:
      raise Exception(f"No weather API providers were found.")

  def get_forecast(lat, lon):
    try:
      WeatherForecast.__lock.acquire()
      timestamp = time.localtime()
      if time.mktime(timestamp) - time.mktime(WeatherForecast.__last_request_time) < 60:
        if WeatherForecast.__last_forecast_data:
          return WeatherForecast.__last_forecast_data

      data = None
      # try different API providers if previous one(s) failed
      for api_provider in WeatherForecast.__api_providers:
        try:
          data = api_provider.forecast(lat, lon)
          if data:
            break
        except Exception as e:
          logger.error(f"{api_provider.name} API failed: {e}")
          continue

      if data:
        WeatherForecast.__last_forecast_data = data
        WeatherForecast.__last_request_time = timestamp
        return data
      else:
        if WeatherForecast.__last_forecast_data:
          # return last good cache if failed, add an indicator too
          WeatherForecast.__last_forecast_data['now']['api_provider'] += '*'
          return WeatherForecast.__last_forecast_data

        # otherwise throw exception
        raise Exception(f"All weather API providers failed.")
    finally:
      WeatherForecast.__lock.release()
