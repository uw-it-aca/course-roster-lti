# UW Course Roster LTI App

[![Build Status](https://github.com/uw-it-aca/course-roster-lti/workflows/Build%2C%20Test%20and%20Deploy/badge.svg?branch=master)](https://github.com/uw-it-aca/course-roster-lti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/course-roster-lti/badge.svg?branch=master)](https://coveralls.io/github/uw-it-aca/course-roster-lti?branch=master)

A Django LTI application for displaying a roster of course people, with official photos

Project settings.py
------------------

**INSTALLED_APPS**

    'course_roster',
    'blti',

**REST client app settings**

    RESTCLIENTS_CANVAS_DAO_CLASS = 'Live'
    RESTCLIENTS_CANVAS_HOST = 'example.instructure.com'
    RESTCLIENTS_CANVAS_OAUTH_BEARER = '...'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    url(r'^roster/', include('course_roster.urls')),
