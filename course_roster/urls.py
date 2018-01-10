from django.conf.urls import url
from course_roster.views import (
    LaunchView, CourseRoster, CourseSections, RosterPhoto)


urlpatterns = [
    url(r'^$', LaunchView.as_view()),
    url(r'^photos/(?P<photo_key>[a-z0-9]*)$', RosterPhoto.as_view()),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/people$',
        CourseRoster.as_view()),
    url(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/sections$',
        CourseSections.as_view()),
]
