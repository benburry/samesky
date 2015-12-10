#!/usr/bin/env python

from flask import Flask, render_template, Response
import googlemaps
import forecastio
import json
import datetime
import pytz
import os
import sys
import subprocess
import tempfile
import shutil
import re


app = Flask(__name__, static_folder='pics')
file_fmt = '%Y-%m-%d_%H-%M'
display_fmt = '%-I:%M %p'
my_address = 'London, UK'
gmaps_key = ''
forecastio_key = ''
geocode_cache = {}
mytimezone = None
display_tz = None
mylatlon = None
camera_opts = {}

try:
    from local_settings import *
except ImportError:
    pass

gmaps = googlemaps.Client(key=gmaps_key)


def geocode_address(address):
    result = geocode_cache.get(address, None)
    if result is None:
        geocode_result = gmaps.geocode(address)
        geocode_result = geocode_result[0]

        latlon = geocode_result['geometry']['location']
        tz_result = gmaps.timezone(latlon)
        timezone = tz_result['timeZoneId']

        display_town = [x['short_name'] for x in geocode_result['address_components']
                if 'postal_town' in x['types'] or 'locality' in x['types']][0]

        result = (timezone, display_town, latlon)
        geocode_cache[address] = result

    return result


def init():
    global display_tz, mytimezone, mylatlon

    timezone, display_town, mylatlon = geocode_address(my_address)
    if not mytimezone:
        mytimezone = timezone

    if not display_tz:
        display_tz = display_town


def writeimage():
    import picamera
    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.utc)
    tmpgifpath = os.path.join(tempfile.gettempdir(), '%s.gif' % now.strftime(file_fmt))
    with picamera.PiCamera() as camera:
        for k, v in camera_opts.iteritems():
            setattr(camera, k, v)
        camera.capture(os.path.join(app.static_folder, '%s.jpg' % now.strftime(file_fmt)), format='jpeg', thumbnail=None)
        camera.capture(tmpgifpath, format='gif')

    prev_gif_filename = '%s.gif' % (now - datetime.timedelta(minutes=1)).strftime(file_fmt)
    prev_gifpath = os.path.join(app.static_folder, prev_gif_filename)
    gifpath = os.path.join(app.static_folder, '%s.gif' % now.strftime(file_fmt))
    try:
        prev_gif_info = subprocess.check_output(['/usr/bin/gifsicle', '-I', prev_gifpath])

        p = re.compile(r'%s (?P<framecount>\d+) image' % prev_gif_filename)
        m = p.search(prev_gif_info)
        framecount = None
        if m:
            framecount = m.group('framecount')

            if int(m.group('framecount')) >= 120:
                subprocess.call(['/usr/bin/gifsicle', '-b', prev_gifpath, '--delete', '"#0"'])
        subprocess.call(['/usr/bin/gifsicle', '-i', prev_gifpath, '--append', tmpgifpath, '--loopcount=forever', '-o', gifpath])
    except:
        shutil.copy(tmpgifpath, gifpath)
    os.remove(tmpgifpath)


def findimage(date, delta):
    day = datetime.timedelta(days=1)
    for targetdate in (
            date - delta,
            date + delta,
            date - delta - day,
            date - delta + day,
            date + delta - day,
            date + delta + day):
        d = '%s.jpg' % targetdate.strftime(file_fmt)
        path = os.path.join(app.static_folder, d)
        if os.path.exists(path):
            return '/'.join((app.static_url_path, d,))


def get_temperature(latlon):
    forecast = forecastio.load_forecast(forecastio_key, latlon['lat'], latlon['lng'], units='us')
    f_temp = forecast.currently().temperature
    c_temp = (f_temp - 32) * 5.0/9.0
    return (f_temp, c_temp)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/samesky/<address>")
def samesky(address):
    timezone, display_town, latlon = geocode_address(address)

    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.utc)
    youtime = now.astimezone(pytz.timezone(timezone))
    metime = now.astimezone(pytz.timezone(mytimezone))

    utcyou = youtime - metime.utcoffset()

    meimg = youimg = None
    x = 0
    while not (meimg and youimg) and x <= 5:
        delta = datetime.timedelta(minutes=x)
        if not meimg:
            meimg = findimage(now, delta)
        if not youimg:
            youimg = findimage(utcyou, delta)
        x += 1

    me_f_temp, me_c_temp = get_temperature(mylatlon)
    you_f_temp, you_c_temp = get_temperature(latlon)

    res = {
        'me': {
            'tz': mytimezone,
            'display_tz': display_tz,
            'time': metime.strftime(display_fmt),
            'img': meimg,
            'temp': {
                'f': int(me_f_temp),
                'c': int(me_c_temp),
            }
        },
        'you': {
            'tz': timezone,
            'display_tz': display_town,
            'time': youtime.strftime(display_fmt),
            'img': youimg,
            'temp': {
                'f': int(you_f_temp),
                'c': int(you_c_temp),
            }
        }
    }

    response = Response(json.dumps(res), mimetype='application/json')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/getpics/<path:timezone>")
def pics(timezone):
    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.utc)
    youtime = now.astimezone(pytz.timezone(timezone))
    metime = now.astimezone(pytz.timezone(mytimezone))

    utcyou = youtime - metime.utcoffset()

    meimg = youimg = None
    x = 0
    while not (meimg and youimg) and x <= 5:
        delta = datetime.timedelta(minutes=x)
        if not meimg:
            meimg = findimage(now, delta)
        if not youimg:
            youimg = findimage(utcyou, delta)
        x += 1

    res = {
        'me': {
            'tz': mytimezone,
            'display_tz': display_tz,
            'time': metime.strftime(display_fmt),
            'img': meimg,
        },
        'you': {
            'tz': timezone,
            'display_tz': timezone.split('/', 2)[1].replace('_', ' '),
            'time': youtime.strftime(display_fmt),
            'img': youimg,
        }
    }

    response = Response(json.dumps(res), mimetype='application/json')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'capture':
        writeimage()
    else:
        init()
        app.run(debug=False, host='0.0.0.0', threaded=True)
