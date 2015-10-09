from django.db import models
from django.conf import settings
from restclients.canvas.users import Users
from restclients.pws import PWS
from datetime import datetime
from django.utils.timezone import make_aware, get_current_timezone
from os import makedirs
from urllib3 import PoolManager


class CanvasAvatar(models.Model):
    """ A model for cacheing avatar urls for Canvas users.
    """
    user_id = models.IntegerField(max_length=16, unique=True)
    url = models.CharField(max_length=1024, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get(self):
        user = Users().get_user(self.user_id)
        self.url = user.avatar_url
        self.save()

        if self.url is None:
            raise Exception("Avatar not available")

        return self._fetch()

    def get_url(self):
        """
        Returns a tuple: url, is_static
        """
        if self.url is None or self.last_updated is None:
            return "/roster/%s/avatar" % self.user_id, False

        now = make_aware(datetime.now(), get_current_timezone())
        delta = now - self.last_updated
        policy = getattr(settings, "CANVAS_AVATAR_CACHE_POLICY", 60 * 60 * 4)
        if (delta.seconds > policy):
            return "/roster/%s/avatar" % self.user_id, False

        return self.url, True

    def _fetch(self):
        cafile = getattr(settings, "RESTCLIENTS_CA_BUNDLE",
                         "/etc/ssl/certs/ca-bundle.crt")
        pool_manager = PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=cafile,
                                   timeout=5)
        return pool_manager.request("GET", self.url)


class IDPhotoAvatar(models.Model):
    """ Handles cacheing idphoto avatars for Canvas users.
    """
    reg_id = models.CharField(max_length=32, unique=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get(self):
        img = PWS().get_idcard_photo(self.reg_id, size=120)
        cache_path = self._cache_path()
        #os.makedirs(cache_path)
        # cache the img file
        #self.save()
        return img

    def get_url(self):
        """
        Returns a tuple: url, is_static
        """
        # TODO: implement cache policy, return static url
        return "/roster/%s/avatar" % self.reg_id, False

    def _cache_path(self):
        bucket = self.reg_id[:3].lower()
        return "/data/canvas/static/photos/%s" % bucket
