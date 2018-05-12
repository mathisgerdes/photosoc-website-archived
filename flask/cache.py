import json


class CacheInterface(object):
    def __init__(self, base_url, urlfetch, cache, timeout,
                 content=None):
        self.cache = cache
        self.urlfetch = urlfetch
        self.base_url = base_url
        self.content = content if content is not None else dict()
        self.timeout = timeout

    def fetch(self, path):
        response = self.urlfetch(self.base_url + path)
        if response.status_code != 200:
            value = None
        else:
            value = response.content
        return value

    def default_update(self, key):
        # by default expect key to be a url
        return self.fetch(key)

    def update(self, key):
        """ Force update of the value saved in cache for key.

        If key is not in self.content, it is passed to default_update.
        If default_update is None, key must be such
        that base_url + key is a url.

        Returns:
            Updated, parsed value of key.
        """
        try:
            # try update with known parse function and path
            path, update_fn = self.content[key]
            value = update_fn(path)
        except KeyError:
            # default update mechanism
            value = self.default_update(key)

        self.cache.set(key, value, timeout=self.timeout)

        return value

    def update_all(self, keys=None):
        """ Update all file names in content.

        Args:
            content: iterable giving the resource keys.
                By default update all entries in self.content.
        """
        if keys is None:
            keys = self.content
        values = []
        for key in keys:
            values.append(self.update(key))
        return values

    def _pretty_print(self, key):
        """ Returns a pretty printed string of the value to key. """
        text = json.dumps(self.cache.get(key), indent=2)
        return text.replace('\n', '<br>').replace(' ', '&nbsp;')

    def __getitem__(self, key):
        """ Get entry; fetch & update the value if it is not in the cache. """
        value = self.cache.get(key)
        if value is None:
            value = self.update(key)
        return value

    def __str__(self):
        values = ['<h3>' + key + '</h3><p>' +
                  self._pretty_print(key) + '</p>'
                  for key in self.content]
        return ('<h2> Cached Values </h2>' +
                '\n'.join(values))
