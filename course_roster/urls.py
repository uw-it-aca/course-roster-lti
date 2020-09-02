from django.urls import re_path
from course_roster.views import (
    LaunchView, CourseRoster, CourseSections, RosterPhoto)

urlpatterns = [
    re_path(r'^$', LaunchView.as_view()),
    re_path(r'^photos/(?P<photo_key>[a-z0-9]*)$',
            RosterPhoto.as_view(), name='photo'),
    re_path(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/people$',
            CourseRoster.as_view()),
    re_path(r'^api/v1/course/(?P<canvas_course_id>[0-9]+)/sections$',
            CourseSections.as_view()),
]
