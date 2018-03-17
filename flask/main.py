from google.appengine.api import urlfetch
from werkzeug.contrib.cache import GAEMemcachedCache
from flask import Flask, render_template, request
from content import Content

import logging

app = Flask(__name__)

# SETTINGS
CONTENT_URL = 'https://mathisgerdes.github.io/photosoc-edinburgh/content/'
app.config.from_object(__name__)

cache = GAEMemcachedCache()
content = Content(cache, urlfetch.fetch, app.config['CONTENT_URL'])

# ROUTES

@app.route('/')
def debug_root():
    try:
        return render_template('index.html', home=content['sites/home.json'])
    except Exception as e:
        return str(e)

@app.route('/admin/content')
def show_content():
    return str(content)

@app.route('/admin/update')
def update_data():
    content.update_all()
    return str(content)
