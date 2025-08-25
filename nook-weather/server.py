#!/usr/bin/env python

import os
import time
import base64

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
  wsgi_logger.setLevel(logging.INFO)

def get_base64_icon(icon_name, icon_ext, static_dir):
  icon_path = os.path.join(static_dir, f"{icon_name}.{icon_ext}")
  try:
    with open(icon_path, "rb") as img_file:
      return "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
  except Exception:
    return ""

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

@app.route('/kindle_image', strict_slashes=False)
def kindle_image():
  try:
    from flask import Response, request
    import os
    import io
    from PIL import Image, ImageOps
    import cairosvg
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'static', 'images')
    # Prepare data for template
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
    # Embed icons as base64 data URIs
    data['now']['icon_data'] = get_base64_icon(data['now']['icon'], data['info']['icon_ext'], static_dir)
    for item in data['hourly']:
      item['icon_data'] = get_base64_icon(item['icon'], data['info']['icon_ext'], static_dir)
    for item in data['daily']:
      item['icon_data'] = get_base64_icon(item['icon'], data['info']['icon_ext'], static_dir)
    svg = render_template('kindle.svg', now=data['now'], hourly=data['hourly'],
             daily=data['daily'], info=data['info'])
    # Convert SVG to PNG (600x800) grayscale
    png_bytes = cairosvg.svg2png(bytestring=svg.encode('utf-8'), output_width=600, output_height=800, background_color='white')
    image = Image.open(io.BytesIO(png_bytes)).convert('L')
    # Ensure white background (in case of transparency)
    image = ImageOps.invert(ImageOps.invert(image).convert('L'))
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return Response(output.read(), mimetype='image/png')
  except Exception as e:
    return f"System error: {e}"

init_logger()
WeatherForecast.init_from_env()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  serve(TransLogger(app), threads=10, ident='Server')
