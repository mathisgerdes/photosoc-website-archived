from google.appengine.api import urlfetch
from werkzeug.contrib.cache import GAEMemcachedCache
from flask import Flask, render_template, request
from content import ContentStore
from flickr import FlickrInterface

import json

app = Flask(__name__)

# SETTINGS
app.config.from_object('config')
# CONSTANTS
SHEETS_URL = 'https://sheets.googleapis.com/v4/'

cache = GAEMemcachedCache()

photos = FlickrInterface(app.config['FLICKR_KEY'],# app.config['CONTENT_PATHS'],
                         urlfetch.fetch, cache, app.config['TIMEOUT'])
content = ContentStore(photos, app.config['GOOGLE_KEY'], app.config['CONTENT_PATHS'],
                       urlfetch.fetch, cache, app.config['TIMEOUT'])


# ROUTES

@app.route('/flickr')
def flickr_test():
    try:
        res = photos.fetch_photo('40995662852')
    except Exception as e:
        return  "Flickr: " + repr(e)
    return json.dumps(res, indent=2).replace('\n', '<br>').replace(' ', '&nbsp;')

@app.route('/')
def debug_root():
    try:
        return render_template('index.html',
                               home=content['home'],
                               events=content['events'])
    except Exception as e:
        return str(e)

@app.route('/admin/content')
def show_content():
    try:
        return '<!doctype html><html><body>' + str(content) + '</body></html>'
    except Exception as e:
        return str(e)

@app.route('/admin/update')
def update_data():
    try:
        content.update_all()
    except Exception as e:
        return str(e)
    return show_content()
