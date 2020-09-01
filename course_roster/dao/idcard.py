from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from uw_pws import PWS
from urllib.parse import urlparse, urlunparse
import random
import string


def cache_key(key):
    return 'idphoto-key-{}'.format(key)


def get_photo(url_key):
    data = cache.get(cache_key(url_key))
    cache.delete(cache_key(url_key))

    if data is None:
        raise ObjectDoesNotExist()

    return PWS().get_idcard_photo(
        data.get('reg_id'), size=data.get('image_size'))


def get_photo_url(reg_id, image_size):
    """ Returns a url for the IDPhoto
    """
    if PWS().valid_uwregid(reg_id):
        url_key = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.digits) for _ in range(16))

        data = {'reg_id': reg_id, 'image_size': image_size}
        expires = getattr(settings, 'IDCARD_TOKEN_EXPIRES', 60 * 60)
        cache.set(cache_key(url_key), data, timeout=expires)

        return "/roster/photos/{}".format(url_key)


def get_avatar_url(url, image_size):
    """ Modifies the passed url based on image_size
    """
    url_parts = urlparse(url)
    if 'gravatar.com' in url_parts.netloc:
        new_parts = url_parts._replace(
            query='s={}&d=mm'.format(image_size))
        return urlunparse(new_parts)
    return url
