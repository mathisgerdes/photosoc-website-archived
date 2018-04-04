import json

TIMEOUT = 60*60*24  # time in seconds; 24h


def parse_time(date_from, date_to, time_from, time_to):
    if date_from and date_to:
        return date_from + ' ' + time_to + ' - ' + date_to + ' ' + time_to
    elif time_to:
        return date_from + ' | ' + time_from + ' - ' + time_to
    else:
        return date_from + ' ' + time_from


def opt_row_item(row, index, default):
    try:
        return row[index] if row[index].strip() else default
    except IndexError:
        return default

class CacheInterface(object):
    def __init__(self, cache, urlfetch, base_url='', content=dict(),
                 default_parse=None):
        self.cache = cache
        self.urlfetch = urlfetch
        self.base_url = base_url
        self.content = content
        self.default_parse = default_parse

    def fetch(self, path):
        response = self.urlfetch(self.base_url + path)
        if response.status_code != 200:
            value = None
        else:
            value = response.content
        return value

    def update(self, key):
        """ Force update of the value saved in cache for key.

        If key is not in self.content, key is expected to be a url
        (i.e. base_url + key is expected to be a valid url).

        Returns:
            Updated, parsed value of key.
        """
        try:
            # try update with known parse function and path
            path, update_fn = self.content[key]
            value = update_fn(path)
        except KeyError:
            # default update mechanism
            value = self.fetch(key)
            if self.default_parse is not None:
                value = self.default_parse(value)

        self.cache.set(key, value, timeout=TIMEOUT)

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

class SpreadsheetsInterface(CacheInterface):
    def __init__(self, google_key, cache, urlfetch, content=dict(),
                 default_parse=None):
        self.google_key = google_key
        CacheInterface.__init__(self, cache, urlfetch,
            'https://sheets.googleapis.com/v4/', content, default_parse)

    def fetch_section(self, path, section):
        """ Fetch a section of a spreadsheet.

        May raise a KeyError.
        """
        row_url = path + '!' + section + '?key=' + self.google_key
        text_response = self.fetch(row_url)
        return json.loads(text_response)['values']

    def fetch_list(self, path, row_from, row_to, start_index=1):
        index = start_index
        while True:
            section = row_from + '%d'%index + ':' + row_to + '%d'%index

            try:
                response = self.fetch_section(path, section)  # raises KeyError
                row = response[0]
                index += 1
                yield row
            except KeyError:  # response does not have the 'values' field
                raise StopIteration


class ContentStore(SpreadsheetsInterface):
    def __init__(self, cache, urlfetch, google_key, paths):
        SpreadsheetsInterface.__init__(self, google_key, cache, urlfetch, {
            'events': (paths['events'], self.update_events),
            'home': (paths['home'], self.update_home)})

    def update_events(self, path):
        events = []

        for row in self.fetch_list(path + 'EventList', 'A', 'I', 2):
            events.append({
                'title': row[0],
                'text': row[5],
                'date': parse_time(row[1], row[2], row[3], row[4]),
                'image': row[6],
                'link': row[7],
                'full_text': row[8]})

        return events

    def update_home(self, path):
        home = dict()

        # general
        response = self.fetch_section(path + 'Main', 'B1:B1')
        home['featured_events'] = [-int(i) for i in response[0][0].split(',')]

        # slides
        slides = []
        for row in self.fetch_list(path + 'Slides', 'B', 'F', 2):
            slides.append({
                'image': row[0],
                'heading': row[1],
                'text': row[2],
                'button': opt_row_item(row, 3, None),
                'button_link': opt_row_item(row, 4, '#')})
        home['slides'] = slides

        # featurettes
        features = []
        for row in self.fetch_list(path + 'Featurettes', 'B', 'G', 2):
            features.append({
                'image': row[0],
                'heading': row[1],
                'heading_muted': row[2],
                'text': row[3],
                'button': opt_row_item(row, 4, None),
                'button_link': opt_row_item(row, 5, '#')})
        home['features'] = features

        return home
