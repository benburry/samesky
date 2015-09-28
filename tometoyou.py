from flask import Flask, render_template, Response
import json
import datetime
import pytz
import os
import sys


app = Flask(__name__, static_folder='pics')
file_fmt = '%Y-%m-%d_%H-%M'
display_fmt = '%a, %-d %B %Y %-I:%M %p'
mytimezone = 'Europe/London'


def writeimage():
    import picamera
    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.utc)
    with picamera.PiCamera() as camera:
        camera.capture(os.path.join(app.static_folder, '%s.jpg' % now.strftime(file_fmt)))


def findimage(date, delta):
    for targetdate in (date - delta, date + delta):
        d = '%s.jpg' % targetdate.strftime(file_fmt)
        path = os.path.join(app.static_folder, d)
        if os.path.exists(path):
            return '/'.join((app.static_url_path, d,))


@app.route("/")
def index():
    return render_template('index.html')


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
        'me': '%s: %s' % (mytimezone, metime.strftime(display_fmt)),
        'you': '%s: %s' % (timezone, youtime.strftime(display_fmt)),
        'meimg': meimg,
        'youimg': youimg
    }

    response = Response(json.dumps(res), mimetype='application/json')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'capture':
        writeimage()
    else:
        app.run(debug=False, host='0.0.0.0', threaded=True)
