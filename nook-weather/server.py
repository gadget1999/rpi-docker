#!/usr/bin/env python

import os
import time
import random

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

cached_data = None
def process_data():
  global cached_data
  try:
    data = get_forecast()

    info = {}
    timestamp = time.localtime()
    info['day'] = time.strftime('%a', timestamp)
    info['date'] = time.strftime('%d', timestamp)
    info['quote'] = get_quote()
    info['api_provider'] = os.environ['WEATHER_API_PROVIDER']
    data['info'] = info

    cached_data = data
    return(data)
  except Exception as e:
    if cached_data:
      # return last good cache if failed
      return cached_data
    # otherwise re-throw the exception
    raise

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/')
def index():
  try:
    data = process_data()
    return render_template('index.html', now=data['now'], hourly=data['hourly']
                                     , daily=data['daily'], info=data['info'])
  except Exception as e:
    return f"System error: {e}"

if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  from waitress import serve
  serve(app, ident='Server')
