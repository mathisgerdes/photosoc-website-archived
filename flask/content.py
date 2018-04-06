import json
from cache import CacheInterface


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


class SpreadsheetsInterface(CacheInterface):
    def __init__(self, google_key, *args, **kwargs):
        self.google_key = google_key
        CacheInterface.__init__(
            self, 'https://sheets.googleapis.com/v4/', *args, **kwargs)

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
    def __init__(self, photos, google_key, paths, urlfetch, cache, timeout):
        self.photos = photos

        SpreadsheetsInterface.__init__(
            self, google_key, urlfetch, cache, timeout, {
                'events': (paths['events'], self.update_events),
                'home': (paths['home'], self.update_home)})

    def parse_image(self, key, flickr_ending):
        if key.startswith('id:'):
            id = key.split(':')[1].strip()
            photo = self.photos.fetch_photo(id)
            return (photo['src_base'] + flickr_ending, photo['url'])
        return (key, None)

    def update_events(self, path):
        events = []

        for row in self.fetch_list(path + 'EventList', 'A', 'I', 2):
            events.append({
                'title': row[0],
                'text': row[5],
                'date': parse_time(row[1], row[2], row[3], row[4]),
                'image': self.parse_image(row[6], '_b.jpg'),
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
                'image': self.parse_image(row[0], '_h.jpg'),
                'heading': row[1],
                'text': row[2],
                'button': opt_row_item(row, 3, None),
                'button_link': opt_row_item(row, 4, '#')})
        home['slides'] = slides

        # featurettes
        features = []
        for row in self.fetch_list(path + 'Featurettes', 'B', 'G', 2):
            features.append({
                'image': self.parse_image(row[0], '_b.jpg'),
                'heading': row[1],
                'heading_muted': row[2],
                'text': row[3],
                'button': opt_row_item(row, 4, None),
                'button_link': opt_row_item(row, 5, '#')})
        home['features'] = features

        return home
