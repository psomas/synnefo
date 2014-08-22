# Copyright (C) 2010-2014 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from synnefo_branding import settings as synnefo_settings
from synnefo.lib import parse_base_url
from astakos.api.services import astakos_services as vanilla_astakos_services
from synnefo.lib import join_urls
from synnefo.lib.services import fill_endpoints

from copy import deepcopy


BASE_URL = getattr(settings, 'ASTAKOS_BASE_URL',
                   'https://accounts.example.synnefo.org')


BASE_HOST, BASE_PATH = parse_base_url(BASE_URL)

astakos_services = deepcopy(vanilla_astakos_services)
fill_endpoints(astakos_services, BASE_URL)
ACCOUNTS_PREFIX = astakos_services['astakos_account']['prefix']
VIEWS_PREFIX = astakos_services['astakos_ui']['prefix']
KEYSTONE_PREFIX = astakos_services['astakos_identity']['prefix']
WEBLOGIN_PREFIX = astakos_services['astakos_weblogin']['prefix']
ADMIN_PREFIX = astakos_services['astakos_admin']['prefix']

# Set the expiration time of newly created auth tokens
# to be this many hours after their creation time.
AUTH_TOKEN_DURATION = getattr(settings, 'ASTAKOS_AUTH_TOKEN_DURATION', 30 * 24)

DEFAULT_USER_LEVEL = getattr(settings, 'ASTAKOS_DEFAULT_USER_LEVEL', 4)

INVITATIONS_PER_LEVEL = getattr(settings, 'ASTAKOS_INVITATIONS_PER_LEVEL', {
    0: 100,
    1: 2,
    2: 0,
    3: 0,
    4: 0
})

ADMINS = tuple(getattr(settings, 'ADMINS', ()))
MANAGERS = tuple(getattr(settings, 'MANAGERS', ()))
HELPDESK = tuple(getattr(settings, 'HELPDESK', ()))

CONTACT_EMAIL = settings.CONTACT_EMAIL
SERVER_EMAIL = settings.SERVER_EMAIL
SECRET_KEY = settings.SECRET_KEY
SESSION_ENGINE = settings.SESSION_ENGINE

# Identity Management enabled modules
# Supported modules are: 'local', 'twitter' and 'shibboleth'
IM_MODULES = getattr(settings, 'ASTAKOS_IM_MODULES', ['local'])

# Force user profile verification
FORCE_PROFILE_UPDATE = getattr(settings, 'ASTAKOS_FORCE_PROFILE_UPDATE', False)

#Enable invitations
INVITATIONS_ENABLED = getattr(settings, 'ASTAKOS_INVITATIONS_ENABLED', False)

COOKIE_NAME = getattr(settings, 'ASTAKOS_COOKIE_NAME', '_pithos2_a')
COOKIE_DOMAIN = getattr(settings, 'ASTAKOS_COOKIE_DOMAIN', None)
COOKIE_SECURE = getattr(settings, 'ASTAKOS_COOKIE_SECURE', True)

IM_STATIC_URL = getattr(settings, 'ASTAKOS_IM_STATIC_URL', '/static/im/')

# If set to False and invitations not enabled newly created user
# will be automatically accepted
MODERATION_ENABLED = getattr(settings, 'ASTAKOS_MODERATION_ENABLED', True)

# Set service name
SITENAME = getattr(settings, 'ASTAKOS_SITENAME', synnefo_settings.SERVICE_NAME)

# Set recaptcha keys
RECAPTCHA_PUBLIC_KEY = getattr(settings, 'ASTAKOS_RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = getattr(settings, 'ASTAKOS_RECAPTCHA_PRIVATE_KEY', '')
RECAPTCHA_OPTIONS = getattr(settings, 'ASTAKOS_RECAPTCHA_OPTIONS',
                            {'theme': 'custom',
                             'custom_theme_widget': 'okeanos_recaptcha'})
RECAPTCHA_USE_SSL = getattr(settings, 'ASTAKOS_RECAPTCHA_USE_SSL', True)
RECAPTCHA_ENABLED = getattr(settings, 'ASTAKOS_RECAPTCHA_ENABLED', False)

# Set where the user should be redirected after logout
LOGOUT_NEXT = getattr(settings, 'ASTAKOS_LOGOUT_NEXT', '')

# Set user email patterns that are automatically activated
RE_USER_EMAIL_PATTERNS = getattr(
    settings, 'ASTAKOS_RE_USER_EMAIL_PATTERNS', [])

# Messages to display on login page header
# e.g. {'warning':
#       'This warning message will be displayed on the top of login page'}
LOGIN_MESSAGES = getattr(settings, 'ASTAKOS_LOGIN_MESSAGES', [])

# Messages to display on login page header
# e.g. {'warning':
#       'This warning message will be displayed on the top of signup page'}
SIGNUP_MESSAGES = getattr(settings, 'ASTAKOS_SIGNUP_MESSAGES', [])

# Messages to display on login page header
# e.g. {'warning':
#       'This warning message will be displayed on the top of profile page'}
PROFILE_MESSAGES = getattr(settings, 'ASTAKOS_PROFILE_MESSAGES', [])

# Messages to display on all pages
# e.g. {'warning':
#       'This warning message will be displayed on the top of every page'}
GLOBAL_MESSAGES = getattr(settings, 'ASTAKOS_GLOBAL_MESSAGES', [])

# messages to display as extra actions in account forms
# e.g. {'https://www.myhomepage.com': 'Back to <service_name>'}
PROFILE_EXTRA_LINKS = getattr(settings, 'ASTAKOS_PROFILE_EXTRA_LINKS', {})

# The number of unsuccessful login requests per minute allowed
# for a specific user
RATELIMIT_RETRIES_ALLOWED = getattr(
    settings, 'ASTAKOS_RATELIMIT_RETRIES_ALLOWED', 3)

# If False the email change mechanism is disabled
EMAILCHANGE_ENABLED = getattr(settings, 'ASTAKOS_EMAILCHANGE_ENABLED', False)

# Set the expiration time (in days) of email change requests
EMAILCHANGE_ACTIVATION_DAYS = getattr(
    settings, 'ASTAKOS_EMAILCHANGE_ACTIVATION_DAYS', 10)

# Set the astakos main functions logging severity (None to disable)
from logging import INFO
LOGGING_LEVEL = getattr(settings, 'ASTAKOS_LOGGING_LEVEL', INFO)

# Set how many objects should be displayed per page
PAGINATE_BY = getattr(settings, 'ASTAKOS_PAGINATE_BY', 50)

# Set how many objects should be displayed per page in show all projects page
PAGINATE_BY_ALL = getattr(settings, 'ASTAKOS_PAGINATE_BY_ALL', 50)

# Enforce token renewal on password change/reset
NEWPASSWD_INVALIDATE_TOKEN = getattr(
    settings, 'ASTAKOS_NEWPASSWD_INVALIDATE_TOKEN', True)

# Interval at which to update the user's available quota in astakos usage
# profile view
USAGE_UPDATE_INTERVAL = getattr(settings, 'ASTAKOS_USAGE_UPDATE_INTERVAL',
                                5000)

# Permit local account migration
ENABLE_LOCAL_ACCOUNT_MIGRATION = getattr(
    settings, 'ASTAKOS_ENABLE_LOCAL_ACCOUNT_MIGRATION', True)

# Migrate eppn identifiers to remote id
SHIBBOLETH_MIGRATE_EPPN = getattr(settings, 'ASTAKOS_SHIBBOLETH_MIGRATE_EPPN',
                                  False)

# Migrate eppn identifiers to remote id
SHIBBOLETH_MIGRATE_EPPN = getattr(settings, 'ASTAKOS_SHIBBOLETH_MIGRATE_EPPN',
                                  False)

# Strict shibboleth usage
SHIBBOLETH_REQUIRE_NAME_INFO = getattr(settings,
                                       'ASTAKOS_SHIBBOLETH_REQUIRE_NAME_INFO',
                                       False)

default_activation_redirect_url = join_urls('/', BASE_PATH, VIEWS_PREFIX,
                                            "landing")
ACTIVATION_REDIRECT_URL = getattr(settings, 'ASTAKOS_ACTIVATION_REDIRECT_URL',
                                  default_activation_redirect_url)

# If true, this enables a ui compatibility layer for the introduction of UUIDs
# in identity management. WARNING: Setting to True will break your installation
TRANSLATE_UUIDS = getattr(settings, 'ASTAKOS_TRANSLATE_UUIDS', False)

# Users that can approve or deny project applications from the web.
PROJECT_ADMINS = getattr(settings, 'ASTAKOS_PROJECT_ADMINS', set())

# OAuth2 Twitter credentials.
TWITTER_TOKEN = getattr(settings, 'ASTAKOS_TWITTER_TOKEN', '')
TWITTER_SECRET = getattr(settings, 'ASTAKOS_TWITTER_SECRET', '')
TWITTER_AUTH_FORCE_LOGIN = getattr(
    settings, 'ASTAKOS_TWITTER_AUTH_FORCE_LOGIN', False)

# OAuth2 Google credentials.
GOOGLE_CLIENT_ID = getattr(settings, 'ASTAKOS_GOOGLE_CLIENT_ID', '')
GOOGLE_SECRET = getattr(settings, 'ASTAKOS_GOOGLE_SECRET', '')

# OAuth2 LinkedIn credentials.
LINKEDIN_TOKEN = getattr(settings, 'ASTAKOS_LINKEDIN_TOKEN', '')
LINKEDIN_SECRET = getattr(settings, 'ASTAKOS_LINKEDIN_SECRET', '')

# URL to redirect the user after successful login when no next parameter is set
default_success_url = join_urls('/', BASE_PATH, VIEWS_PREFIX, "landing")
LOGIN_SUCCESS_URL = getattr(settings, 'ASTAKOS_LOGIN_SUCCESS_URL',
                            default_success_url)

# A way to extend the components presentation metadata
COMPONENTS_META = getattr(settings, 'ASTAKOS_COMPONENTS_META', {})

# A way to extend the resources presentation metadata
RESOURCES_META = getattr(settings, 'ASTAKOS_RESOURCES_META', {})

# Do not require email verification for new users
SKIP_EMAIL_VERIFICATION = getattr(settings,
                                  'ASTAKOS_SKIP_EMAIL_VERIFICATION', False)

# Kamaki download url. Displayed in api access view
API_CLIENT_URL = getattr(settings, 'ASTAKOS_API_CLIENT_URL',
                         'https://pypi.python.org/pypi/kamaki')

KAMAKI_CONFIG_CLOUD_NAME = getattr(settings,
                                   'ASTAKOS_KAMAKI_CONFIG_CLOUD_NAME',
                                   None)

REDIRECT_ALLOWED_SCHEMES = getattr(settings,
                                   'ASTAKOS_REDIRECT_ALLOWED_SCHEMES',
                                   ('pithos', 'pithosdev'))

ADMIN_STATS_PERMITTED_GROUPS = getattr(settings,
                                       'ASTAKOS_ADMIN_STATS_PERMITTED_GROUPS',
                                       ['admin-stats'])

ENDPOINT_CACHE_TIMEOUT = getattr(settings,
                                 'ASTAKOS_ENDPOINT_CACHE_TIMEOUT',
                                 60)

RESOURCE_CACHE_TIMEOUT = getattr(settings,
                                 'ASTAKOS_RESOURCE_CACHE_TIMEOUT',
                                 60)

ADMIN_API_ENABLED = getattr(settings, 'ASTAKOS_ADMIN_API_ENABLED', False)

_default_project_members_limit_choices = (
    ('Unlimited', 'Unlimited'),
    ('5', '5'),
    ('15', '15'),
    ('50', '50'),
    ('100', '100')
)

PROJECT_MEMBERS_LIMIT_CHOICES = getattr(settings,
                                 'ASTAKOS_PROJECT_MEMBERS_LIMIT_CHOICES',
                                 _default_project_members_limit_choices)

ADMIN_API_PERMITTED_GROUPS = getattr(settings,
                                     'ASTAKOS_ADMIN_API_PERMITTED_GROUPS',
                                     ['admin-api'])

# Default settings for AUTH_LDAP
AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn",
                           "email": "mail"}
AUTH_LDAP_ALWAYS_UPDATE_USER = False
