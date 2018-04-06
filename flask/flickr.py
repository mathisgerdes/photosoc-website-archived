import json

from cache import CacheInterface


class FlickrInterface(CacheInterface):
    def __init__(self, flickr_key, *args, **kwargs):
        self.flickr_key = flickr_key
        CacheInterface.__init__(
            self, 'https://api.flickr.com/services/rest/?', *args, **kwargs)

    def fetch_flickr(self, variables):
        response = self.fetch('format=json&nojsoncallback=1&api_key=' +
                              self.flickr_key + '&' + '&'.join(variables))
        answer = json.loads(response)
        if answer['stat'] != 'ok':
            return None  # bad request
        return answer

    def fetch_photo(self, id):
        variables = ['method=flickr.photos.getInfo', 'photo_id='+id]
        photo_resp = self.fetch_flickr(variables)['photo']

        photo = dict()
        photo['url'] = photo_resp['urls']['url'][0]['_content']
         # + _h .jpg to turn into high-res photo
        photo['src_base'] = 'https://farm%s.staticflickr.com/%s/%s_%s' % (
            photo_resp['farm'], photo_resp['server'], id, photo_resp['secret'])
        photo['owner_name'] = photo_resp['owner']['realname']
        photo['owner_uname'] = photo_resp['owner']['username']
        photo['owner_url'] = 'https://www.flickr.com/people/' + photo_resp['owner']['nsid']

        return photo

class PhotoStore(FlickrInterface):
    def __init__(self, flickr_key, cache, urlfetch, timeout):
        FlickrInterface.__init__(
            self, flickr_key, cache, urlfetch, timeout,
            default_update=self.photo_update)
