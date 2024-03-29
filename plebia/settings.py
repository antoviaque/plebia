# -*- coding: utf-8 -*-

import os
import sys
import logging

# Shortcuts to the real site directory and its parent.
spath = lambda x: os.path.join(os.path.dirname(__file__), x)
ppath = lambda x: os.path.join(os.path.dirname(
                                     os.path.dirname(__file__)), x)

# Django settings for plebia project.

DELUGE_COMMAND = [u'/usr/local/bin/deluge-console']
FFMPEG_PATH = u'/usr/local/bin/ffmpeg'
FFMPEG2THEORA_PATH = u'/usr/bin/ffmpeg2theora'
UNRAR_PATH = u'/usr/bin/unrar'

DOWNLOAD_DIR = u'/var/www/downloads/'

TEST_DOWNLOAD_DIR = spath(u'tests/')
TEST_VIDEO_PATH = ppath(u'eben_moglen-freedom_in_the_cloud.avi')
TEST_SHORT_VIDEO_PATH = ppath(u'creative_commons.webm')
TEST_SERIES_LIST = ['Pioneer One']
TEST_DB_DUMP_PATH = u'/tmp/plebia_test_db.json'
CACHE_DIR = spath(u'cache/')
LOCK_PATH = ppath(u'plebia/')
BIN_DIR = ppath(u'bin/')
STATIC_DIR = ppath(u'static/')

CACHE_BACKEND = 'db://plebia_cache'

SOFTWARE_NAME="Plebia"
SOFTWARE_VERSION=0.1
SOFTWARE_USER_AGENT="%s/%f" % (SOFTWARE_NAME, SOFTWARE_VERSION)

# BitTorrent
BITTORRENT_PORTS=(6881, 6891)
BITTORRENT_MAX_METADATA_DOWNLOADS=50
BITTORRENT_METADATA_TIMEOUT=1200
BITTORRENT_MAX_DOWNLOADS=10
BITTORRENT_DOWNLOAD_NOSEED_TIMEOUT=3600
BITTORRENT_MAX_SEEDS=5

PROXIES = None

HTTP_REQUESTS_DELAY=3

DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOG_LEVEL=logging.INFO
LOG_FILE=ppath('server.log')
RAISE_EXCEPTION_ON_ERROR=False 

MAX_TRANSCODING_PROCESSES=1

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': spath('db/plebia.sqlite'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '_rjr7_fqo-1tcxx6izkqt+xk(3+h%&5k)vc6w$q9+nj+42xc=a'

# Specify a list of regular expressions of module paths to exclude
# from the coverage analysis. Examples are ``'tests$'`` and ``'urls$'``.
# This setting is optional.
COVERAGE_MODULE_EXCLUDES = ['tests$', 'settings$', 'urls$', 'locale$',
                            'common.views.test', '__init__', 'django',
                            'migrations', 'tastypie', 'south']


# Specify the directory where you would like the coverage report to create
# the HTML files.
# You'll need to make sure this directory exists and is writable by the
# user account running the test.
# You should probably set this one explicitly in your own settings file.
COVERAGE_REPORT_HTML_OUTPUT_DIR = spath('../static/tests/')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'plebia.urls'

TEMPLATE_DIRS = (
    spath('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'south',
    'tastypie',
    'django_coverage',
    'wall',
    'djangoplugins',
)

from settings_local import *

# Run tests in memory
if 'test' in sys.argv or 'testserver' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'sqlite3'}

