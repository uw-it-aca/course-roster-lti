from django.conf.urls import patterns, url, include
from course_roster.views import CourseRoster, CourseSections


urlpatterns = patterns(
    'course_roster.views',
    url(r'^$', 'Main'),
    url(r'^photos/(?P<photo_key>[a-z0-9]*)$', 'RosterPhoto'),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/people$',
        CourseRoster().run),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/sections$',
        CourseSections().run),
)
