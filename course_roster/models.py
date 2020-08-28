from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from uw_pws import PWS
from urllib.parse import urlparse, urlunparse
from logging import getLogger
import threading
import random
import string

logger = getLogger(__name__)


class IDPhoto(object):
    """ Retrieves idphoto images for Canvas users.
    """
    def __init__(self, **kwargs):
        self.expire_seconds = 60 * 60 * 4

    def _cache_key(self, key):
        return 'idphoto-key-{}'.format(key)

    def get(self, url_key):
        data = cache.get(self._cache_key(url_key))
        cache.delete(self._cache_key(url_key))

        if data is None:
            raise ObjectDoesNotExist()

        return PWS().get_idcard_photo(
            data.get('reg_id'), size=data.get('image_size'))

    def get_url(self, reg_id, image_size):
        """ Returns a url for the IDPhoto
        """
        if PWS().valid_uwregid(self.reg_id):
            url_key = ''.join(random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for _ in range(16))

            cache_key = self._cache_key(url_key)
            data = {'reg_id': reg_id, 'image_size': image_size}
            cache.set(cache_key, data, timeout=self.expire_seconds)

            return "/roster/photos/{}".format(url_key)

    def get_avatar_url(self, url):
        """ Modifies the passed url based on self.image_size
        """
        url_parts = urlparse(url)
        if 'gravatar.com' in url_parts.netloc:
            new_parts = url_parts._replace(
                query='s={}&d=mm'.format(self.image_size))
            return urlunparse(new_parts)
        return url
