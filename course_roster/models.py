from django.db import models
from restclients.pws import PWS
import random
import string


class IDPhoto(models.Model):
    """ Retrieves idphoto images for Canvas users.
    """
    url_key = models.CharField(max_length=16, unique=True)
    reg_id = models.CharField(max_length=32)
    date_created = models.DateTimeField(auto_now=True)

    def get(self):
        self.delete()
        return PWS().get_idcard_photo(self.reg_id, size=120)

    def get_url(self):
        """ Returns a url for the IDPhoto
        """
        if not self.url_key:
            self.url_key = ''.join(random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for _ in range(16))
            self.save()
        return "/roster/photos/%s" % self.url_key
