from django.conf import settings
from rc_django.cache_implementation.memcache import MemcachedCache


class IDCardPhotoCache(MemcachedCache):
    def get_cache_expiration_time(self, service, url):
        if 'pws' == service:
            return getattr(settings, 'IDCARD_PHOTO_EXPIRES', 60 * 60)
