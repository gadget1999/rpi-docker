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
  api_provider = os.environ['WEATHER_API_PROVIDER']
  key = os.environ['WEATHER_API_KEY']
  gps = os.environ['GPS_COORDINATES'].split(",")
  lat = gps[0]
  lon = gps[1]
  if api_provider.lower() == "openweather":
    api = OpenWeatherAPI(key)
  elif api_provider.lower() == "nws":
    api = NWSAPI(key)
  elif api_provider.lower() == "darksky":
    api = DarkSkyAPI(key)
  else:
    raise Exception(f"Unknown weather API provider: {api_provider}")

  return api.forecast(lat, lon)

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
    logger.info(f"Forecast: {data['now']['temp']}")

    info = {}
    info['day'] = time.strftime('%a', timestamp)
    info['date'] = time.strftime('%d', timestamp)
    info['quote'] = get_quote()
    info['api_provider'] = os.environ['WEATHER_API_PROVIDER']
    data['info'] = info

    cached_data = data
    return(data)
  except Exception as e:
    logger.error(f"Failed to get forecast: {e}")
    if cached_data:
      # return last good cache if failed, add an indicator too
      cached_data['info']['api_provider'] += '*'
      return cached_data
    # otherwise re-throw the exception
    raise
  finally:
    lock.release()

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/')
def index():
  try:
    data = process_data()
    return render_template('index.html', now=data['now'], hourly=data['hourly']
                                     , daily=data['daily'], info=data['info'])
  except Exception as e:
    return f"System error: {e}"

AppName = "nook-weather"
LOGFILE = f"/tmp/{AppName}.log"
logger = logging.getLogger(f"{AppName}")
def init_logger():
  fileHandler = logging.FileHandler(LOGFILE)
  fileHandler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(message)s"))
  logger.addHandler(fileHandler)
  logger.setLevel(logging.INFO)

init_logger()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  from waitress import serve
  serve(app, ident='Server')
