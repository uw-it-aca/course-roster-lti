from django.db import models
from restclients.pws import PWS
from urlparse import urlparse, urlunparse
from urllib import urlencode
import random
import string


class IDPhoto(models.Model):
    """ Retrieves idphoto images for Canvas users.
    """
    url_key = models.CharField(max_length=16, unique=True)
    reg_id = models.CharField(max_length=32)
    image_size = models.IntegerField()
    date_created = models.DateTimeField(auto_now=True)

    def get(self):
        self.delete()
        return PWS().get_idcard_photo(self.reg_id, size=self.image_size)

    def get_url(self):
        """ Returns a url for the IDPhoto
        """
        if not self.url_key:
            self.url_key = ''.join(random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for _ in range(16))
            self.save()
        return "/roster/photos/%s" % self.url_key

    def get_avatar_url(self, url):
        """ Modifies the passed url based on self.image_size
        """
        url_parts = urlparse(url)
        if 'gravatar.com' in url_parts.netloc:
            new_parts = url_parts._replace(
                query=urlencode({'s': self.image_size, 'd': 'mm'})
            )
            return urlunparse(new_parts)
        return url
