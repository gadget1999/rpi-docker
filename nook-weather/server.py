#!/usr/bin/env python

import os
import sys
import time
import random
from pprint import pprint

from DarkSky import DarkSkyAPI
from OpenWeather import OpenWeatherAPI

from flask import Flask
from flask import render_template

def get_quote():
  try:
    debug = os.environ.get('DEBUG', None)
    if debug:
      return "DEBUG"

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
  except:
    e = sys.exc_info()[0]
    return str(e)

def get_forecast():
  api_provider = os.environ['WEATHER_API_PROVIDER']
  key = os.environ['WEATHER_API_KEY']
  gps = os.environ['GPS_COORDINATES'].split(",")
  lat = gps[0]
  lon = gps[1]
  if api_provider.lower() == "openweather":
    api = OpenWeatherAPI(key)
  elif api_provider.lower() == "darksky":
    api = DarkSkyAPI(key)

  return api.forecast(lat, lon)

def process_data():
  data = get_forecast()

  info = {}
  timestamp = time.localtime()
  info['day'] = time.strftime('%a', timestamp)
  info['date'] = time.strftime('%d', timestamp)
  info['quote'] = get_quote()
  info['api_provider'] = os.environ['WEATHER_API_PROVIDER']

  data['info'] = info
  return(data)

def check_os_env(variables):
  for variable in variables:
    if variable not in os.environ:
      print(f"ERROR Please set the environment variables: {variable}")
      sys.exit(1)

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/')
def index():
  """ index page function. """
  data = process_data()
  return render_template('index.html', now=data['now'], hourly=data['hourly']
                                     , daily=data['daily'], info=data['info'])

if __name__ == '__main__':
  variables = ['WEATHER_API_PROVIDER', 'WEATHER_API_KEY', 'GPS_COORDINATES']
  check_os_env(variables)

  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  from waitress import serve
  serve(app)
