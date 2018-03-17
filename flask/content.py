import json


# SPECIFIC UPDATE FUNCTIONS
def update_events(store, events):
    for event in events:
        store.update(event['file'])
    return events


CONTENT = {
    'sites/home.json': (json.loads, None),
    'events/events.json': (json.loads, update_events)
}

TIMEOUT = 60*60*24  # time in seconds; 24h


class ContentStore(object):
    def __init__(self, cache, urlfetch, base_url):
        self.cache = cache
        self.fetch = urlfetch
        self.base_url = base_url

    def update_cache(self, fname, parse_fn=None, update_fn=None):
        """ Fetch file with given name and update cached value.

        Args:
            fname: File name relative to base_url (same as key in cache).
            parse_fn: Function to parse the plain text content of the file.
                Default keeps the plain text.
            update_fn: Function to further process the datastructure.
                Might invoke update/update_all again, with dynamic dependents.
        """
        result = self.fetch(self.base_url + fname)
        if result.status_code != 200:
            value = None
        else:
            if parse_fn is None:
                value = result.content
            else:
                value = parse_fn(result.content)
            if update_fn is not None:
                value = update_fn(self, value)
        self.cache.set(fname, value, timeout=TIMEOUT)

        return value

    def update(self, fname):
        """ Force update of the value saved in cache for fname and dependents.

        Returns:
            Updated, parsed value of fname.
        """
        try:
            # update with known parse_fn and update_fn
            value = self.update_cache(fname, *CONTENT[fname])
        except KeyError:
            if fname.split('.')[-1].lower() == 'json':
                value = self.update_cache(fname, json.loads)
            else:
                # do not parse content (i.e. plain text)
                value = self.update_cache(fname)
        return value

    def update_all(self, content=CONTENT):
        """ Update all file names in content.

        Args:
            content: iterable giving the file names (e.g. list or dict).
        """
        values = []
        for fname in content:
            values.append(self.update(fname))
        return values

    def __getitem__(self, name):
        """ Get item, fetch/update the value if it is not in the cache. """
        value = self.cache.get(name)
        if value is None:
            value = self.update(name)
        return value

    def _pretty_print(self, fname):
        text = json.dumps(self.cache.get(fname), indent=2)
        return text.replace('\n', '<br>').replace(' ', '&nbsp;')

    def __str__(self):
        values = ['<h2>' + fname + '</h2><p>' +
                  self._pretty_print(fname) + '</p>'
                  for fname in CONTENT]
        return ('<!doctype html><html><body><h1> Cached Values </h1>' +
                '\n'.join(values) + '</body></html>')
