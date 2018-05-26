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

photos = FlickrInterface(app.config['FLICKR_KEY'],
                         urlfetch.fetch, cache, app.config['TIMEOUT'])
content = ContentStore(photos, app.config['GOOGLE_KEY'],
                       app.config['CONTENT_PATHS'],
                       urlfetch.fetch, cache, app.config['TIMEOUT'])


# ROUTES
@app.route('/')
def root():
    return render_template('index.html',
                           general=content['general'],
                           page=content['home_page'],
                           events=content['events'],)

@app.route('/events')
def events():
    return render_template('events.html',
                           general=content['general'],
                           events=content['events'],
                           page=content['event_page'])

@app.route('/equipment')
def equipment():
    return render_template('equipment.html',
                           general=content['general'],
                           equipment=content['equipment'],
                           page=content['equipment_page'])

@app.route('/committee')
def committee():
    return render_template('committee.html',
                           general=content['general'],
                           page=content['committee_page'],
                           committee=content['committee'],
                           years=sorted(content['committee'].keys(), reverse=True))

@app.route('/about')
def about():
    return render_template('about.html',
                           general=content['general'])

@app.route('/admin/force_update')
def force_update():
    try:
        content.update_all()
    except Exception as e:
        return str(e)
    return "Done."
