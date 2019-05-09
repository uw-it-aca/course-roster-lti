import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/course-roster-lti>`_.
"""

# The VERSION file is created by travis-ci, based on the tag name
version_path = 'course_roster/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='UW-Course-Roster-LTI',
    version=VERSION,
    packages=['course_roster'],
    include_package_data=True,
    install_requires = [
        'Django>=2.1,<2.2',
        'django-blti>=2.1.2',
        'UW-RestClients-Core>=1.1.1,<2.0',
        'UW-RestClients-Canvas>=1.0.9,<2.0',
        'UW-RestClients-PWS>=2.0,<3.0',
    ],
    license='Apache License, Version 2.0',
    description='Display a roster of UW course people, with official photos',
    long_description=README,
    url='https://github.com/uw-it-aca/course-roster-lti',
    author = "UW-IT AXDD",
    author_email = "aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
