from django.conf.urls import patterns, url, include
from course_roster.views import (
    LaunchView, CourseRoster, CourseSections, RosterPhoto)


urlpatterns = patterns(
    '',
    url(r'^$', LaunchView.as_view()),
    url(r'^photos/(?P<photo_key>[a-z0-9]*)$', RosterPhoto.as_view()),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/people$',
        CourseRoster().run),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/sections$',
        CourseSections().run),
)
