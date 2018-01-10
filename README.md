UW Course Roster LTI App
===========================

A Django LTI application for displaying a roster of course people, with official photos

Installation
------------

**Project directory**

Install the app in your project.

    $ cd [project]
    $ pip install UW-Course-Roster-LTI

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
