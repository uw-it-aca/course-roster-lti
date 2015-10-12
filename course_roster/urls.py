from django.conf.urls import patterns, url, include
from course_roster.views import CourseRoster


urlpatterns = patterns('course_roster.views',
    url(r'^$', 'Main'),
    url(r'^photos/(?P<photo_key>[a-z0-9]*)$', 'IDPhoto'),
    url(r'^api/v1/roster', CourseRoster().run),
)
