#!/usr/bin/env python

import os
import time
import random

from flask import Flask
from flask import render_template
from waitress import serve
from paste.translogger import TransLogger

from weather.Forecast import WeatherForecast
from misc.quotes import Quotes

import logging
logger = logging.getLogger()

def get_quote():
  try:
    quote_file = os.environ['QUOTE_FILE']
    Quotes.init_quotes(quote_file)
    return Quotes.get_one_quote()
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
  info['now'] = time.strftime('%H:%M:%S', timestamp)
  info['quote'] = get_quote()
  info['icon_path'] = 'static/images'
  info['icon_ext'] = 'png'
  data['info'] = info
  return data

AppName = "nook-weather"
def init_logger():
  # Flask logging (application logs)
  app_logfile = f"/tmp/{AppName}.log"

  try:
    fileHandler = logging.FileHandler(app_logfile)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(message)s"))
    logger.addHandler(fileHandler)
  except Exception as e: 
    print(f"Cannot open log file: {e}")

  logger.setLevel(logging.INFO)
  # Waitress access logging (web server logs)
  wsgi_logger = logging.getLogger('wsgi')
  access_logfile = f"/tmp/{AppName}-access.log"
  wsgi_logger.addHandler(logging.FileHandler(access_logfile))
  wsgi_logger.setLevel(logging.DEBUG)

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/forecast')
def index():
  try:
    data = process_data()
    return render_template('index.html', now=data['now'], hourly=data['hourly'],
             daily=data['daily'], info=data['info'])
  except Exception as e:
    return f"System error: {e}"

init_logger()
WeatherForecast.init_from_env()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  serve(TransLogger(app), ident='Server')
