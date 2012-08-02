# Django settings for quota project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

COMMISSIONING_APP_NAME = None

if not COMMISSIONING_APP_NAME:
    from os import environ
    if 'COMMISSIONING_APP_NAME' not in environ:
        m = ("Cannot determine COMMISSIONING_APP_NAME from "
             "settings.py or getenv()")
        raise ValueError(m)

    COMMISSIONING_APP_NAME = environ['COMMISSIONING_APP_NAME']

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

from commissioning.utils.pvdata import getpv

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'holder',                       # Or path to database file if using sqlite3.
        'USER': 'holder',                       # Not used with sqlite3.
        'PASSWORD': getpv('klapeto'),           # Not used with sqlite3.
        'HOST': 'dev84.dev.grnet.gr',           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                         # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Athens'

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

# Absolute path to the directory that holds media.
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
SECRET_KEY = 'ee=*x%x6sp=hcm7j4zzkvpam27g*7*d59fca-q!azaqma!jx*+'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.transaction.TransactionMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'commissioning.servers.django_server.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)


INSTALLED_APPS = (
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.sessions',
    #'django.contrib.sites',
    #'django.contrib.messages',
    'commissioning.controllers.django_controller',
    'commissioning.servers.django_server.server_app',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

names = COMMISSIONING_APP_NAME.split(',')
names = ('commissioning.servers.%s.django_backend' % (n,) for n in names)
from django.utils.importlib import import_module

applist = []
for name in names:
    try:
        import_module(name)
        applist.append(name)
    except ImportError:
        pass

INSTALLED_APPS += tuple(applist)

