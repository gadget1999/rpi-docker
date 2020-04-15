#!/usr/bin/env python

import os
import time
import random
import logging
from threading import RLock

from DarkSky import DarkSkyAPI
from OpenWeather import OpenWeatherAPI
from NWS import NWSAPI

from flask import Flask
from flask import render_template

def get_quote():
  try:
    debug = os.environ.get('DEBUG', None)
    if debug:
      return ["DEBUG"]

    quotes_folder="/quotes"
    quote_filename=random.choice(os.listdir(quotes_folder))
    quote_file=os.path.join(quotes_folder, quote_filename)
    lines=[]
    with open(quote_file, 'r') as quotefile:
      line = quotefile.readline()
      while line:
        line=line.strip()
        if (line):
          lines.append(line)
        line = quotefile.readline()
    return lines
  except Exception as e:
    return [f"Failed to get quote: {e}"]

def get_forecast():
  gps = os.environ['GPS_COORDINATES'].split(",")
  lat = gps[0]
  lon = gps[1]

  # try different API providers if previous one(s) failed
  global api_providers
  for api_provider in api_providers:
    try:
      return api_provider.forecast(lat, lon)
    except Exception as e:
      logger.error(f"{api_provider.name} API failed: {e}")
      continue

  # if it comes here, means all providers failed
  raise Exception(f"All weather API providers failed.")

lock = RLock()
last_request_time = time.localtime(0)
cached_data = None
def process_data():
  global last_request_time
  global cached_data
  try:
    lock.acquire()
    timestamp = time.localtime()
    if time.mktime(timestamp) - time.mktime(last_request_time) < 60:
      if cached_data:
        return cached_data

    data = get_forecast()
    last_request_time = timestamp
    logger.info(f"Temperature: {data['now']['temp']} ({data['now']['cond']})")

    info = {}
    info['day'] = time.strftime('%a', timestamp)
    info['date'] = time.strftime('%d', timestamp)
    info['quote'] = get_quote()
    data['info'] = info

    cached_data = data
    return(data)
  except Exception as e:
    logger.error(f"Failed to get forecast: {e}")
    if cached_data:
      # return last good cache if failed, add an indicator too
      cached_data['now']['api_provider'] += '*'
      return cached_data
    # otherwise re-throw the exception
    raise
  finally:
    lock.release()

api_providers = []
def init_forecast_api_providers():
  global api_providers

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
    api_providers.append(api_provider)

  if not api_providers:
    raise Exception(f"No weather API providers were found.")

AppName = "nook-weather"
LOGFILE = f"/tmp/{AppName}.log"
logging.raiseException = False
logger = logging.getLogger(f"{AppName}")
def init_logger():
  if os.path.isfile(LOGFILE):
    fileHandler = logging.FileHandler(LOGFILE)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(message)s"))
    logger.addHandler(fileHandler)
  logger.setLevel(logging.INFO)

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/')
def index():
  try:
    data = process_data()
    return render_template('index.html', now=data['now'], hourly=data['hourly']
                                     , daily=data['daily'], info=data['info'])
  except Exception as e:
    return f"System error: {e}"

init_logger()
init_forecast_api_providers()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  from waitress import serve
  serve(app, ident='Server')
