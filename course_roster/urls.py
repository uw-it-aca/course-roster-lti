from django.conf.urls import patterns, url, include
from course_roster.views import CourseRoster


urlpatterns = patterns('course_roster.views',
    url(r'^$', 'Main'),
    url(r'^(?P<user_id>[^/]*)/avatar$', 'Avatar'),
    url(r'^api/v1/roster', CourseRoster().run),
)
