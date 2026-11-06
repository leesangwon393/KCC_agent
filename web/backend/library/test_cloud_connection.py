import hashlib
import io
import json
import os
import secrets
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from .models import AgentLink, AppleIdentity, AppleLoginAttempt, MacPairing


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class AppleLoginTests(TestCase):
    def setUp(self):
        self.config = patch('library.apple_auth.configured', return_value=True)
        self.config.start()
        self.addCleanup(self.config.stop)

    def start(self):
        response = self.client.get('/api/v1/auth/apple/start/')
        self.assertEqual(response.status_code, 302)
        cookie = response.cookies['moa_apple_browser']
        self.assertTrue(cookie['secure'])
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'None')
        from urllib.parse import parse_qs, urlsplit
        return parse_qs(urlsplit(response.url).query)['state'][0]

    @patch('library.apple_auth.exchange', return_value={'sub': 'apple-subject', 'email': 'existing@example.com'})
    def test_login_uses_subject_and_rejects_replay(self, exchange):
        existing = get_user_model().objects.create_user('existing', email='existing@example.com')
        state = self.start()
        response = self.client.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'})
        self.assertEqual(response.url, '/#connection')
        identity = AppleIdentity.objects.get(subject='apple-subject')
        self.assertNotEqual(identity.owner, existing)
        self.assertEqual(int(self.client.session['_auth_user_id']), identity.owner_id)
        self.assertFalse(identity.owner.has_usable_password())
        self.client.cookies['moa_apple_browser'] = 'replay'
        response = self.client.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'})
        self.assertIn('invalid_state', response.url)
        self.assertEqual(exchange.call_count, 1)
        state = self.start()
        self.client.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'})
        self.assertEqual(AppleIdentity.objects.count(), 1)

    @patch('library.apple_auth.exchange')
    def test_state_is_browser_bound_and_expires(self, exchange):
        state = self.start()
        other = Client()
        self.assertIn('invalid_state', other.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'}).url)
        AppleLoginAttempt.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertIn('invalid_state', self.client.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'}).url)
        exchange.assert_not_called()

    @patch('library.apple_auth.exchange', side_effect=ValueError('bad token'))
    def test_failed_verification_never_logs_in(self, exchange):
        state = self.start()
        response = self.client.post('/api/v1/auth/apple/callback/', {'state': state, 'code': 'code'})
        self.assertIn('verification_failed', response.url)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(AppleIdentity.objects.count(), 0)

    def test_unconfigured_login_is_disabled(self):
        with patch('library.apple_auth.configured', return_value=False):
            self.assertFalse(self.client.get('/api/v1/auth/config/').json()['apple_enabled'])
            self.assertEqual(self.client.get('/api/v1/auth/apple/start/').status_code, 503)


class PairingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('owner')
        self.other = get_user_model().objects.create_user('other')

    def ticket(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/v1/agent/pairing/', {}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        return response.json()['pairing_secret']

    def consume(self, secret):
        return Client().post('/api/v1/agent/pairing/consume/', {'pairing_secret': secret}, content_type='application/json')

    def test_login_and_csrf_required_to_issue_ticket(self):
        self.assertEqual(self.client.post('/api/v1/agent/pairing/').status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/v1/agent/pairing/').status_code, 403)

    def test_token_is_one_use_and_owner_bound(self):
        secret = self.ticket()
        ticket = MacPairing.objects.get()
        self.assertEqual(ticket.secret_hash, digest(secret))
        response = self.consume(secret)
        self.assertEqual(response.status_code, 200)
        link = AgentLink.objects.get()
        self.assertEqual(link.owner, self.user)
        self.assertEqual(link.token_hash, digest(response.json()['bridge_token']))
        self.assertEqual(self.consume(secret).status_code, 403)
        client = Client()
        client.force_login(self.other)
        self.assertEqual(client.get('/api/v1/agent/status/').json()['links'], [])

    def test_expiry_and_reissue(self):
        old = self.ticket()
        new = self.ticket()
        self.assertEqual(self.consume(old).status_code, 403)
        MacPairing.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.consume(new).status_code, 403)
        self.assertEqual(AgentLink.objects.count(), 0)


@override_settings(MOA_CLOUD_ORIGIN='https://moa.example.com')
class LocalCloudTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, MOA_LOCAL_KEY='secret', MOA_LOCAL_DATA=self.temp.name)
        self.env.start()
        self.addCleanup(self.env.stop)
        get_user_model().objects.create_user('local-owner')
        self.client = Client(HTTP_HOST='localhost', REMOTE_ADDR='127.0.0.1')
        self.body = {'origin': 'https://moa.example.com', 'pairing_secret': secrets.token_urlsafe(48)}

    def post(self, body=None, **kwargs):
        return self.client.post('/api/v1/local/cloud/connect/', body or self.body, content_type='application/json', **kwargs)

    @patch('urllib.request.urlopen')
    def test_only_pinned_origin_and_localhost_are_allowed(self, urlopen):
        for origin in ['http://moa.example.com', 'https://evil.example', 'https://moa.example.com@evil.example', 'https://moa.example.com/path']:
            self.assertEqual(self.post({**self.body, 'origin': origin}).status_code, 400)
        self.assertEqual(self.post(REMOTE_ADDR='192.168.1.2').status_code, 404)
        urlopen.assert_not_called()

    @patch('urllib.request.urlopen')
    def test_saves_private_token_and_starts_local_session(self, urlopen):
        token = secrets.token_urlsafe(48)
        urlopen.return_value.__enter__.return_value = io.BytesIO(json.dumps({'bridge_token': token}).encode())
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(token, response.content.decode())
        config = Path(self.temp.name) / 'cloud.json'
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(config.read_text())['bridge_token'], token)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(urlopen.call_count, 1)

    def test_csrf_required_without_local_session(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST='localhost', REMOTE_ADDR='127.0.0.1')
        self.assertEqual(client.post('/api/v1/local/cloud/connect/', self.body, content_type='application/json').status_code, 403)


class AppleTokenVerificationTests(TestCase):
    def test_real_signature_audience_expiry_and_nonce_validation(self):
        import time
        import jwt
        from cryptography.hazmat.primitives.asymmetric import ec, rsa
        from cryptography.hazmat.primitives import serialization
        from types import SimpleNamespace
        from .apple_auth import exchange

        with TemporaryDirectory() as directory:
            key_path = Path(directory) / 'apple.p8'
            signing = ec.generate_private_key(ec.SECP256R1())
            key_path.write_bytes(signing.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            apple_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            now = int(time.time())
            claims = {'iss': 'https://appleid.apple.com', 'aud': 'moa.web', 'sub': 'apple-user', 'iat': now, 'exp': now + 600, 'nonce': 'expected'}
            def response(value, key=apple_key):
                token = jwt.encode(value, key, algorithm='RS256', headers={'kid': 'apple-key'})
                return io.BytesIO(json.dumps({'id_token': token}).encode())
            with override_settings(APPLE_TEAM_ID='TEAM', APPLE_KEY_ID='KEY', APPLE_CLIENT_ID='moa.web', APPLE_PRIVATE_KEY_PATH=str(key_path)), \
                 patch('library.apple_auth.urlopen') as urlopen, patch('library.apple_auth.jwt.PyJWKClient') as jwks:
                jwks.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=apple_key.public_key())
                urlopen.return_value.__enter__.return_value = response(claims)
                self.assertEqual(exchange('code', 'expected')['sub'], 'apple-user')
                for fields in [{'aud': 'another-app'}, {'iss': 'https://evil.example'}, {'exp': now - 600}, {'nonce': 'wrong'}]:
                    urlopen.return_value.__enter__.return_value = response({**claims, **fields})
                    with self.assertRaises((ValueError, jwt.PyJWTError)):
                        exchange('code', 'expected')
                other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                urlopen.return_value.__enter__.return_value = response(claims, other_key)
                with self.assertRaises(jwt.InvalidSignatureError):
                    exchange('code', 'expected')


class DisconnectTests(TestCase):
    def test_bearer_can_remove_only_its_own_link(self):
        user = get_user_model().objects.create_user('owner')
        other = get_user_model().objects.create_user('other')
        token = secrets.token_urlsafe(48)
        own = AgentLink.objects.create(owner=user, token_hash=digest(token))
        untouched = AgentLink.objects.create(owner=other, token_hash=digest('another'))
        path = '/api/v1/agent/pairing/disconnect/'
        self.assertEqual(self.client.post(path).status_code, 403)
        response = self.client.post(path, HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AgentLink.objects.filter(pk=own.pk).exists())
        self.assertTrue(AgentLink.objects.filter(pk=untouched.pk).exists())
        self.assertEqual(self.client.post(path, HTTP_AUTHORIZATION='Bearer ' + token).status_code, 403)
