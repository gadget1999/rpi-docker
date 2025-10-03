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

# Helper to get weather data from request (handles zip/gps and process_data)
def get_weather_data_from_request(req):
  zip_code = req.args.get('zip_code') if len(req.args) > 0 else None
  gps_coordinates = req.args.get('gps_coordinates') if len(req.args) > 0 else None
  if not gps_coordinates:
    if zip_code:
      gps_coordinates = WeatherUtils.get_gps_coordinates(zip_code)
    if not gps_coordinates:
      gps_coordinates = os.getenv('GPS_COORDINATES')
  if not gps_coordinates:
    raise Exception(f"""
                    GPS coordinates cannot be found.<p>
                    Please provide gps_coordinates or zip_code as query parameter, 
                    or set GPS_COORDINATES environment variable when starting docker container.<p>
                    Examples:<br>
                    {request.scheme}://{request.host}{request.path}?gps_coordinates=39.7128,-76.0060<br>
                    {request.scheme}://{request.host}{request.path}?zip_code=10001
                    """)
  lat, lon = gps_coordinates.split(",")
  # Inline process_data logic
  data = WeatherForecast.get_forecast(lat, lon)
  logger.debug(f"Weather data from {data['now']['api_provider']} @ {data['now']['time']}")
  info = {}
  report_time = time.strptime(data['now']['time'], '%Y-%m-%d %H:%M:%S')
  timestamp = time.localtime()
  info['day'] = time.strftime('%a', timestamp)
  info['date'] = time.strftime('%d', timestamp)
  info['report_time'] = time.strftime('%b-%d %H:%M:%S', report_time)
  info['fetch_time'] = time.strftime('%H:%M:%S', timestamp)
  info['location'] = f"{round(float(lat))},{round(float(lon))}"
  info['quote'] = Quotes.get_one_quote()
  info['icon_path'] = '/static/images'
  info['icon_ext'] = 'png'
  data['info'] = info
  return data

AppName = "nook-weather"
def init_logger():
  # Flask logging (application logs)
  app_logfile = f"/tmp/{AppName}.log"  
  log_level = logging.INFO
  if 'DEBUG' in os.environ:
    log_level = logging.DEBUG

  try:
    fileHandler = logging.FileHandler(app_logfile)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(message)s"))
    logger.addHandler(fileHandler)
  except Exception as e: 
    print(f"Cannot open log file: {e}")

  logger.setLevel(log_level)
  # Disable Waitress logging
  logging.getLogger('waitress').setLevel(logging.WARN)
  # Waitress access logging (web server logs)
  wsgi_logger = logging.getLogger('wsgi')
  access_logfile = f"/tmp/{AppName}-access.log"
  wsgi_logger.addHandler(logging.FileHandler(access_logfile))
  wsgi_logger.setLevel(log_level)

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
    logger.debug(f"Request args: {request.args}")
    data = get_weather_data_from_request(request)
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
    data = get_weather_data_from_request(request)
    # Embed icons as base64 data URIs
    data['now']['icon_data'] = get_base64_icon(data['now']['icon'], data['info']['icon_ext'], static_dir)
    for item in data['hourly']:
      item['icon_data'] = get_base64_icon(item['icon'], data['info']['icon_ext'], static_dir)
    for item in data['daily']:
      item['icon_data'] = get_base64_icon(item['icon'], data['info']['icon_ext'], static_dir)
    logger.debug(f"Rendering SVG...")
    svg = render_template('kindle.svg', now=data['now'], hourly=data['hourly'],
             daily=data['daily'], info=data['info'])
    # Convert SVG to PNG (600x800) grayscale
    logger.debug(f"Converting SVG to PNG...")
    png_bytes = cairosvg.svg2png(bytestring=svg.encode('utf-8'), output_width=600, output_height=800, background_color='white')    
    image = Image.open(io.BytesIO(png_bytes)).convert('L')
    # Ensure white background (in case of transparency)
    logger.debug(f"Converting image to grayscale...")
    image = ImageOps.invert(ImageOps.invert(image).convert('L'))
    output = io.BytesIO()
    logger.debug(f"Saving PNG to output stream...")
    image.save(output, format='PNG')
    output.seek(0)
    logger.debug(f"Returning PNG response...")
    return Response(output.read(), mimetype='image/png')
  except Exception as e:
    return f"System error: {e}"

init_logger()
WeatherForecast.init_from_env()
if __name__ == '__main__':
  app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
  serve(TransLogger(app), threads=10, ident='Server')
