from .base_urls import *
from django.conf.urls import include
from django.urls import re_path


urlpatterns += [
    re_path(r'^', include('course_roster.urls')),
    re_path(r'^blti/', include('blti.urls')),
]
