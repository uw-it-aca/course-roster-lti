from .base_settings import *

DEBUG = True if os.getenv('ENV', 'localdev') == 'localdev' else False

INSTALLED_APPS += [
    'course_roster.apps.CourseRosterConfig',
    'compressor',
]

COMPRESS_ROOT = "/static/"
COMPRESS_PRECOMPILERS = (("text/less", "lessc {infile} {outfile}"),)
COMPRESS_OFFLINE = True
STATICFILES_FINDERS += ("compressor.finders.CompressorFinder",)

COURSE_ROSTER_PER_PAGE = 50

if os.getenv('ENV', 'localdev') == 'localdev':
    RESTCLIENTS_MEMCACHED_SERVERS = ('127.0.0.1:11211',)

LOGGING = {}
