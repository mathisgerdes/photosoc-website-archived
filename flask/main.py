from google.appengine.api import urlfetch
from werkzeug.contrib.cache import GAEMemcachedCache
from flask import Flask, render_template, request
from content import ContentStore

import json

app = Flask(__name__)

# SETTINGS
app.config.from_object('config')
# CONSTANTS
SHEETS_URL = 'https://sheets.googleapis.com/v4/'

cache = GAEMemcachedCache()
store = ContentStore(cache, urlfetch.fetch,
                     app.config['GOOGLE_KEY'],
                     app.config['CONTENT_PATHS'],
                     app.config['TIMEOUT'])

# ROUTES

@app.route('/flickr')
def flickr_test():
    try:
        url = "https://api.flickr.com/services"
        response = urlfetch.fetch(app.config['FLICKR_API_URL']+'method=flickr.test.echo&name=value')
        if response.status_code != 200:
            return "Error, http error"
        answer = json.loads(response.content)
        if answer['stat'] != 'ok':
            return "Error, answer fail"
        return json.dumps(answer)
    except Exception as e:
        return  str(e)

@app.route('/')
def debug_root():
    try:
        return render_template('index.html',
                               home=store['home'],
                               events=store['events'])
    except Exception as e:
        return str(e)

@app.route('/admin/content')
def show_content():
    try:
        return '<!doctype html><html><body>' + str(store) + '</body></html>'
    except Exception as e:
        return str(e)

@app.route('/admin/update')
def update_data():
    try:
        store.update_all()
    except Exception as e:
        return str(e)
    return show_content()
