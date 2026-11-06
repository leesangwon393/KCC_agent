"""Apple authorization-code login with browser-bound, one-use state."""
import hashlib
import ipaddress
import json
from datetime import timedelta
from pathlib import Path
import secrets
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import AppleIdentity, AppleLoginAttempt

COOKIE = 'moa_apple_browser'
ISSUER = 'https://appleid.apple.com'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def configured():
    origin = urlsplit(settings.MOA_PUBLIC_ORIGIN)
    try:
        ipaddress.ip_address(origin.hostname or '')
        return False
    except ValueError:
        pass
    return bool(origin.scheme == 'https' and origin.hostname and origin.hostname != 'localhost'
                and origin.path in ('', '/') and not origin.query and not origin.fragment
                and not origin.username and not origin.password
                and settings.APPLE_CLIENT_ID and settings.APPLE_TEAM_ID and settings.APPLE_KEY_ID
                and settings.APPLE_PRIVATE_KEY_PATH and Path(settings.APPLE_PRIVATE_KEY_PATH).is_file())


@require_GET
def config(request):
    response = JsonResponse({'apple_enabled': configured(), 'cloud_origin': settings.MOA_PUBLIC_ORIGIN,
                             'local_helper_url': 'http://127.0.0.1:8000/',
                             'setup_required': 'Apple 로그인에는 HTTPS 도메인과 Apple Developer 설정이 필요합니다.'})
    response['Cache-Control'] = 'no-store'
    return response


@require_GET
def start(request):
    if not configured():
        return JsonResponse({'detail': 'Apple 로그인 설정이 준비되지 않았습니다.'}, status=503)
    now = timezone.now()
    AppleLoginAttempt.objects.filter(expires_at__lt=now).delete()
    state, browser, nonce = (secrets.token_urlsafe(32) for _ in range(3))
    AppleLoginAttempt.objects.create(state_hash=digest(state), browser_hash=digest(browser),
                                    nonce=nonce, expires_at=now + timedelta(minutes=10))
    response = HttpResponseRedirect(ISSUER + '/auth/authorize?' + urlencode({
        'client_id': settings.APPLE_CLIENT_ID,
        'redirect_uri': settings.MOA_PUBLIC_ORIGIN + '/api/v1/auth/apple/callback/',
        'response_type': 'code', 'response_mode': 'form_post', 'scope': 'email',
        'state': state, 'nonce': nonce,
    }))
    # Apple posts cross-site; the normal session cookie deliberately stays Lax.
    response.set_cookie(COOKIE, browser, max_age=600, secure=True, httponly=True,
                        samesite='None', path='/api/v1/auth/apple/')
    response['Cache-Control'] = 'no-store'
    return response


def exchange(code, nonce):
    now = int(time.time())
    secret = jwt.encode({'iss': settings.APPLE_TEAM_ID, 'iat': now, 'exp': now + 300,
                         'aud': ISSUER, 'sub': settings.APPLE_CLIENT_ID},
                        Path(settings.APPLE_PRIVATE_KEY_PATH).read_text(), algorithm='ES256',
                        headers={'kid': settings.APPLE_KEY_ID})
    body = urlencode({'client_id': settings.APPLE_CLIENT_ID, 'client_secret': secret,
                      'code': code, 'grant_type': 'authorization_code',
                      'redirect_uri': settings.MOA_PUBLIC_ORIGIN + '/api/v1/auth/apple/callback/'}).encode()
    with urlopen(Request(ISSUER + '/auth/token', data=body,
                         headers={'Content-Type': 'application/x-www-form-urlencoded'}), timeout=15) as response:
        token = json.load(response)['id_token']
    key = jwt.PyJWKClient(ISSUER + '/auth/keys', timeout=15).get_signing_key_from_jwt(token)
    claims = jwt.decode(token, key.key, algorithms=['RS256'], audience=settings.APPLE_CLIENT_ID,
                        issuer=ISSUER, options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'nonce']})
    if not secrets.compare_digest(str(claims['nonce']), nonce) or not isinstance(claims['sub'], str) or not claims['sub']:
        raise ValueError('Invalid Apple identity')
    return claims


@csrf_exempt  # Apple's cross-site form POST is protected by state + browser cookie.
@require_POST
def callback(request):
    error = None
    if not configured():
        error = 'not_configured'
    state, browser = request.POST.get('state', ''), request.COOKIES.get(COOKIE, '')
    attempt = None
    if not error and state and browser and len(state) < 200 and len(browser) < 200:
        with transaction.atomic():
            attempt = AppleLoginAttempt.objects.filter(state_hash=digest(state), browser_hash=digest(browser),
                                                       consumed_at=None, expires_at__gt=timezone.now()).first()
            if attempt and not AppleLoginAttempt.objects.filter(pk=attempt.pk, consumed_at=None).update(consumed_at=timezone.now()):
                attempt = None
    if not error and not attempt:
        error = 'invalid_state'
    if not error and (request.POST.get('error') or not request.POST.get('code')):
        error = 'cancelled'
    if not error:
        try:
            claims = exchange(request.POST['code'], attempt.nonce)
            with transaction.atomic():
                identity = AppleIdentity.objects.filter(subject=claims['sub']).select_related('owner').first()
                if identity is None:
                    user = get_user_model().objects.create_user('apple_' + secrets.token_hex(16))
                    identity = AppleIdentity.objects.create(subject=claims['sub'], owner=user)
                if not identity.owner.is_active:
                    raise ValueError('Inactive account')
            login(request, identity.owner, backend='django.contrib.auth.backends.ModelBackend')
        except (ValueError, KeyError, OSError, jwt.PyJWTError):
            error = 'verification_failed'
    response = HttpResponseRedirect('/#connection' + ('?apple_error=' + error if error else ''))
    response.delete_cookie(COOKIE, path='/api/v1/auth/apple/', samesite='None')
    response['Cache-Control'] = 'no-store'
    return response
