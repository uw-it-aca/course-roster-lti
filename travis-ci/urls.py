from django.conf.urls import include, url


urlpatterns = [
    url(r'^', include('course_roster.urls')),
]
