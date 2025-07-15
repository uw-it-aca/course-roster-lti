from .base_settings import *

INSTALLED_APPS += [
    'course_roster.apps.CourseRosterConfig',
    'compressor',
]

COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (('text/less', 'lessc {infile} {outfile}'),)
COMPRESS_OFFLINE = True
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    RESTCLIENTS_DAO_CACHE_CLASS = 'course_roster.cache.IDCardPhotoCache'

COURSE_ROSTER_PER_PAGE = 50
IDCARD_PHOTO_EXPIRES = 60 * 60 * 2
IDCARD_TOKEN_EXPIRES = 60 * 60 * 2

MIDDLEWARE += [
    'blti.middleware.LTISessionAuthenticationMiddleware',
]
