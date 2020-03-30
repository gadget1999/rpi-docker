#!/usr/bin/env python

import os
import sys
import json
#from time import time.localtime, time.strftime, tzset, tzname
import time
import requests
import random
from flask import Flask
from flask import render_template
from pprint import pprint

DARK_SKY = {
    "api_url": "https://api.darksky.net/forecast",
    "img_url": "/static/images",
    "img_ext": "png"
}

def get_weather():
  global DARK_SKY
  key = str(os.environ['DARKSKY_API_KEY'])
  gps = str(os.environ['GPS_COORDINATES'])
  units = str(os.environ['DARKSKY_API_UNITS'])
  lang = str(os.environ['DARKSKY_API_LANG'])
  url = '{}/{}/{}?units={}&lang={}'.format(DARK_SKY['api_url'], key, gps,units,lang)
  r = requests.get(url)
  return(r.json())
  # with open('sample.json') as fh:
  #   return(json.load(fh))

def compass(bearing):
  coords = {
    'N':  [0, 22.5],
    'NE': [22.5, 67.5],
    'E':  [67.5, 112.5],
    'SE': [112.5, 157.5],
    'S':  [157.5, 202.5],
    'SW': [202.5, 247.5],
    'W':  [247.5, 292.5],
    'NW': [292.5, 337.5],
    'N':  [337.5, 360]
  }
  for k,v in coords.items():
    if bearing >= v[0] and bearing < v[1]:
      return k

def format_time(tz, format, utime):
  os.environ['TZ'] = tz
  time.tzset()
  return time.strftime(format, time.localtime(utime))

def get_quote():
  try:
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

def process_data():
  data = get_weather()
  tz = data['timezone']
  unixtime = data['currently']['time']
  now = data['currently']
  now['time'] = format_time(tz, '%a, %b %d %Y', unixtime)
  now['timestamp'] = format_time(tz, '%Y-%m-%d %H:%M:%S', unixtime)
  now['weekday'] = format_time(tz, '%a', unixtime)
  now['day'] = format_time(tz, '%d', unixtime)
  # only available when all stations are reporing
  # now['hour'] = data['minutely']['summary']
  now['summary'] =  data['hourly']['summary']
  now['high'] = data['daily']['data'][0]['temperatureHigh']
  now['low'] =  data['daily']['data'][0]['temperatureLow']
  now['forecast'] = data['daily']['summary']
  now['windDir'] = compass(int(data['currently']['windBearing']))
  now['dailyquote'] = get_quote()

  hourly = list()
  for i in [3, 6, 9, 12, 15, 18]:
    forecast = data['hourly']['data'][i]
    time = format_time(tz, '%-I %p', int(forecast['time']))
    hourly.append({"time": time, "icon": forecast['icon'],
                   "temp": forecast['temperature']})

  daily = list()
  for i in range(1, 7):
    forecast = data['daily']['data'][i]
    date = format_time(tz, '%m/%d', int(forecast['time']))
    day  = format_time(tz, '%a', int(forecast['time']))
    daily.append(
        {"day": day, "date": date, "icon": forecast['icon'],
         "high": forecast['temperatureHigh'],
         "low":  forecast['temperatureLow']
        })
  return({'now': now, 'hourly': hourly, 'daily': daily})

app = Flask(__name__)
@app.route('/')
def index():
  """ index page function. """
  global DARK_SKY
  pd = process_data()
  return render_template('index.html', now=pd['now'], hourly=pd['hourly']
                                     , daily=pd['daily'], ds=DARK_SKY)

if __name__ == '__main__':
  if 'DARKSKY_API_KEY' not in os.environ:
    print("ERROR Please set the environment variable DARKSK_API_KEY")
    sys.exit(1)
  from waitress import serve
  serve(app, host="0.0.0.0", port=int(os.environ['BIND_PORT']), threads=10)
