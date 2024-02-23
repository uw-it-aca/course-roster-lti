# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from memcached_clients import RestclientPymemcacheClient


class IDCardPhotoCache(RestclientPymemcacheClient):
    def get_cache_expiration_time(self, service, url, status=None):
        if 'pws' == service:
            return getattr(settings, 'IDCARD_PHOTO_EXPIRES', 60 * 60)
