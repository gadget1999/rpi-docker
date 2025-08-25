#!/usr/bin/env python

import os
import time

from flask import Flask, request
from flask import render_template
from waitress import serve
from paste.translogger import TransLogger

from weather.Forecast import WeatherForecast
from misc.quotes import Quotes
from weather.utils import WeatherUtils

import logging
logger = logging.getLogger()

def get_quote():
  try:
    quote_file = os.environ['QUOTE_FILE']
    Quotes.init_quotes(quote_file)
    return Quotes.get_one_quote()
  except Exception as e:
    return [f"Failed to get quote: {e}"]

def process_data(lat, lon):
  data = WeatherForecast.get_forecast(lat, lon)
  info = {}
  report_time = time.strptime(data['now']['time'], '%Y-%m-%d %H:%M:%S')
  timestamp = time.localtime()
  info['day'] = time.strftime('%a', timestamp)
  info['date'] = time.strftime('%d', timestamp)
  info['report_time'] = time.strftime('%b-%d %H:%M:%S', report_time)
  info['fetch_time'] = time.strftime('%H:%M:%S', timestamp)
  info['location'] = f"{round(float(lat))},{round(float(lon))}"
  info['quote'] = get_quote()
  info['icon_path'] = '/static/images'
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
  # Disable Waitress logging
  logging.getLogger('waitress').setLevel(logging.WARN)
  # Waitress access logging (web server logs)
  wsgi_logger = logging.getLogger('wsgi')
  access_logfile = f"/tmp/{AppName}-access.log"
  wsgi_logger.addHandler(logging.FileHandler(access_logfile))
  wsgi_logger.setLevel(logging.DEBUG)

app = Flask(__name__, static_folder='static', template_folder='templates')
@app.route('/forecast', strict_slashes=False)
def forecast():
  try:
    zip_code = None
    gps_coordinates = None
    if len(request.args) > 0:
      zip_code = request.args.get('zip_code')
      gps_coordinates = request.args.get('gps_coordinates')
    if not gps_coordinates:
      if zip_code:
        gps_coordinates = WeatherUtils.get_gps_coordinates(zip_code)
      if not gps_coordinates:
        gps_coordinates = os.environ['GPS_COORDINATES']
    gps = gps_coordinates.split(",")
    lat = gps[0]
    lon = gps[1]
    data = process_data(lat, lon)
    return render_template('index.html', now=data['now'], hourly=data['hourly'],
             daily=data['daily'], info=data['info'])
  except Exception as e:
    return f"System error: {e}"

@app.route('/kindle', strict_slashes=False)
def kindle():
  try:
    import imgkit
    from flask import Response, request
    url = f"{request.scheme}://{request.host}/forecast"
    options = {'format': 'png', 'width': 600, 'height': 800, 'encoding': "UTF-8", 'grayscale': ''}
    #config = imgkit.config(wkhtmltoimage="/tmp/bin/wkhtmltoimage.exe")
    img = imgkit.from_url(url, False, options=options)
    return Response(img, mimetype='image/png')
  except Exception as e:
    return f"System error: {e}"

init_logger()
WeatherForecast.init_from_env()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  serve(TransLogger(app), threads=10, ident='Server')
