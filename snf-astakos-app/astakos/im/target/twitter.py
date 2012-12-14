# Copyright 2011-2012 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

import json

from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404

from urlparse import urlunsplit, urlsplit

from astakos.im.util import prepare_response, get_context
from astakos.im.views import (
    requires_anonymous, render_response, requires_auth_provider)
from astakos.im.settings import ENABLE_LOCAL_ACCOUNT_MIGRATION, BASEURL
from astakos.im.models import AstakosUser, PendingThirdPartyUser
from astakos.im.forms import LoginForm
from astakos.im.activation_backends import get_backend, SimpleBackend
from astakos.im import settings
from astakos.im import auth_providers

import astakos.im.messages as astakos_messages

import logging

logger = logging.getLogger(__name__)

import oauth2 as oauth
import cgi

consumer = oauth.Consumer(settings.TWITTER_TOKEN, settings.TWITTER_SECRET)
client = oauth.Client(consumer)

request_token_url = 'http://twitter.com/oauth/request_token'
access_token_url = 'http://twitter.com/oauth/access_token'
authenticate_url = 'http://twitter.com/oauth/authenticate'


@requires_auth_provider('twitter', login=True)
@require_http_methods(["GET", "POST"])
def login(request):
    resp, content = client.request(request_token_url, "GET")
    if resp['status'] != '200':
        messages.error(request, 'Invalid Twitter response')
        return HttpResponseRedirect(reverse('edit_profile'))

    request.session['request_token'] = dict(cgi.parse_qsl(content))
    url = "%s?oauth_token=%s" % (authenticate_url,
        request.session['request_token']['oauth_token'])

    return HttpResponseRedirect(url)


@requires_auth_provider('twitter', login=True)
@require_http_methods(["GET", "POST"])
def authenticated(
    request,
    template='im/third_party_check_local.html',
    extra_context={}):

    if not 'request_token' in request.session:
        messages.error(request, 'Twitter handshake failed')
        return HttpResponseRedirect(reverse('edit_profile'))

    token = oauth.Token(request.session['request_token']['oauth_token'],
        request.session['request_token']['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    # Step 2. Request the authorized access token from Twitter.
    resp, content = client.request(access_token_url, "GET")
    if resp['status'] != '200':
        try:
          del request.session['request_token']
        except:
          pass
        messages.error(request, 'Invalid Twitter response')
        return HttpResponseRedirect(reverse('edit_profile'))

    access_token = dict(cgi.parse_qsl(content))
    userid = access_token['user_id']
    username = access_token.get('screen_name', userid)
    provider_info = {'screen_name': username}
    affiliation = 'Twitter.com'

    # an existing user accessed the view
    if request.user.is_authenticated():
        if request.user.has_auth_provider('twitter', identifier=userid):
            return HttpResponseRedirect(reverse('edit_profile'))

        # automatically add eppn provider to user
        user = request.user
        if not request.user.can_add_auth_provider('twitter',
                                                  identifier=userid):
            messages.error(request, 'Account already exists.')
            return HttpResponseRedirect(reverse('edit_profile'))

        user.add_auth_provider('twitter', identifier=userid,
                               affiliation=affiliation,
                               provider_info=provider_info)
        messages.success(request, 'Account assigned.')
        return HttpResponseRedirect(reverse('edit_profile'))

    try:
        # astakos user exists ?
        user = AstakosUser.objects.get_auth_provider_user(
            'twitter',
            identifier=userid
        )
        if user.is_active:
            # authenticate user
            return prepare_response(request,
                                    user,
                                    request.GET.get('next'),
                                    'renew' in request.GET)
        else:
            message = user.get_inactive_message()
            messages.error(request, message)
            return HttpResponseRedirect(reverse('login'))

    except AstakosUser.DoesNotExist, e:
        provider = auth_providers.get_provider('twitter')
        if not provider.is_available_for_create():
            messages.error(request,
                           _(astakos_messages.AUTH_PROVIDER_NOT_ACTIVE) % provider.get_title_display)
            return HttpResponseRedirect(reverse('login'))

        # eppn not stored in astakos models, create pending profile
        user, created = PendingThirdPartyUser.objects.get_or_create(
            third_party_identifier=userid,
            provider='twitter',
        )
        # update pending user
        user.affiliation = affiliation
        user.info = json.dumps(provider_info)
        user.generate_token()
        user.save()

        extra_context['provider'] = 'twitter'
        extra_context['provider_title'] = 'Twitter'
        extra_context['token'] = user.token
        extra_context['signup_url'] = reverse('signup') + \
                                    "?third_party_token=%s" % user.token

        return render_response(
            template,
            context_instance=get_context(request, extra_context)
        )

