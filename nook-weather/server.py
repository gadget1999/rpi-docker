#!/usr/bin/env python

import os
import time
import random

from flask import Flask
from flask import render_template

from weather.Forecast import WeatherForecast

import logging
logger = logging.getLogger()

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

def process_data():
  gps = os.environ['GPS_COORDINATES'].split(",")
  lat = gps[0]
  lon = gps[1]
  data = WeatherForecast.get_forecast(lat, lon)

  info = {}
  timestamp = time.localtime()
  info['day'] = time.strftime('%a', timestamp)
  info['date'] = time.strftime('%d', timestamp)
  info['quote'] = get_quote()
  info['icon_path'] = 'static/images'
  info['icon_ext'] = 'png'
  data['info'] = info

  return data

AppName = "nook-weather"
LOGFILE = f"/tmp/{AppName}.log"
logging.raiseException = False
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
WeatherForecast.init_from_env()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  from waitress import serve
  serve(app, ident='Server')
