import json

CONTENT = {
    'sites/home.json': (json.loads, None),
    'sites/nonexistent.json': (json.loads, None),
}

TIMEOUT = 60*60*24  # time in seconds; 24h

class Content(object):
    def __init__(self, cache, urlfetch, base_url):
        self.cache = cache
        self.fetch = urlfetch
        self.base_url = base_url

    def update_cache(self, name, parse_fn=None, update_fn=None):
        """ Fetch file with given name and update cached value.

        Args:
            name: File name relative to base_url (same as key in cache).
            parse_fn: Function to parse the plain text content of the file.
                Default keeps the plain text.
            update_fn: Function to further process the datastructure.
                Might invoke update/update_all again, with dynamic dependents.
        """
        result = self.fetch(self.base_url + name)
        if result.status_code != 200:
            content = None
        elif parse_fn is None:
            content = result.content
        else:
            content = parse_fn(result.content)
        self.cache.set(name, content, timeout=TIMEOUT)

        return content

    def update(self, fname):
        """ Force update of the content saved in cache for fname and dependents.

        Returns:
            Updated, parsed content of fname.
        """
        try:
            # update with known parse_fn and update_fn
            content = self.update_cache(fname, *CONTENT[fname])
        except KeyError:
            if fname.split('.')[-1].lower() == 'json':
                content = self.update_cache(fname, json.loads)
            else:
                # do not parse content (i.e. plain text)
                content = self.update_cache(fname)
        return content

    def update_all(self, content=CONTENT):
        """ Update all file names in content.

        Args:
            content: iterable giving the file names (e.g. list or dict).
        """
        values = []
        for name in content:
            values.append(self.update(name))
        return values

    def __getitem__(self, name):
        """ Get item, fetch/update the value if it is not in the cache. """
        content = self.cache.get(name)
        if content is None:
            content = self.update(name)
        return content

    def pretty_print(self, key):
        text = json.dumps(self.cache.get(key), indent=2)
        return text.replace('\n', '<br>').replace(' ', '&nbsp;')

    def __str__(self):
        objects = ['<h2>' + key + '</h2><p>' +
                   self.pretty_print(key) + '</p>'
                   for key in CONTENT]
        return ('<!doctype html><html><body><h1> Cached Values </h1>' +
                '\n'.join(objects) + '</body></html>')
