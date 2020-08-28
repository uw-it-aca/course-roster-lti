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
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

LOGGING = {}
