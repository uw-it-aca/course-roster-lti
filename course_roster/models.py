from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from bmemcached import Client
from bmemcached.exceptions import MemcachedException
from uw_pws import PWS
from urllib.parse import urlparse, urlunparse
from logging import getLogger
import threading
import pickle
import random
import string

logger = getLogger(__name__)


class IDPhotoTokenCache(object):
    def __init__(self):
        self.expire_seconds = 60 * 60 * 4
        self._set_client()

    def delete_data(self, key):
        try:
            return self.client.delete(key)
        except MemcachedException as ex:
            logger.error('MemCache Delete(key: {}) => {}'.format(key, ex))

    def get_data(self, key):
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data, encoding='utf8')
        except MemcachedException as ex:
            logger.error('MemCache Get(key: {}) => {}'.format(key, ex))

    def set_data(self, key, data):
        try:
            self.client.set(key, pickle.dumps(data), time=self.expire_seconds)
        except MemcachedException as ex:
            logger.error('MemCache Set(key: {}) => {}'.format(key, ex))

    def _set_client(self):
        thread_id = threading.current_thread().ident
        if not hasattr(IDPhotoTokenCache, '_memcached_cache'):
            IDPhotoTokenCache._memcached_cache = {}

        if thread_id in IDPhotoTokenCache._memcached_cache:
            self.client = IDPhotoTokenCache._memcached_cache[thread_id]
            return

        servers = getattr(settings, 'RESTCLIENTS_MEMCACHED_SERVERS', [])
        self.client = Client(servers)
        IDPhotoTokenCache._memcached_cache[thread_id] = self.client


class IDPhoto(object):
    """ Retrieves idphoto images for Canvas users.
    """
    def __init__(self, **kwargs):
        self.url_key = kwargs.get('url_key')
        self.reg_id = kwargs.get('reg_id')
        self.image_size = kwargs.get('image_size')
        self._cache = IDPhotoTokenCache()

    def get(self):
        data = self._cache.get_data(self.url_key)
        self._cache.delete_data(self.url_key)

        if data is None:
            raise ObjectDoesNotExist()

        return PWS().get_idcard_photo(
            data.get('reg_id'), size=data.get('image_size'))

    def get_url(self):
        """ Returns a url for the IDPhoto
        """
        if PWS().valid_uwregid(self.reg_id):
            if not self.url_key:
                self.url_key = ''.join(random.SystemRandom().choice(
                    string.ascii_lowercase + string.digits) for _ in range(16))

                self._cache.set_data(self.url_key, {
                    'reg_id': self.reg_id, 'image_size': self.image_size})

            return "/roster/photos/{}".format(self.url_key)

    def get_avatar_url(self, url):
        """ Modifies the passed url based on self.image_size
        """
        url_parts = urlparse(url)
        if 'gravatar.com' in url_parts.netloc:
            new_parts = url_parts._replace(
                query='s={}&d=mm'.format(self.image_size))
            return urlunparse(new_parts)
        return url
