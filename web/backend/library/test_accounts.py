from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import Client, TestCase

from .models import AgentLink


class RegistrationTests(TestCase):
    def setUp(self):
        self.body = {'username': 'New_Member', 'nickname': '테스트 사용자',
                     'password': 'Maple!River-4796-Sky', 'password_confirm': 'Maple!River-4796-Sky'}

    def signup(self, **changes):
        return self.client.post('/api/v1/auth/signup/', {**self.body, **changes}, content_type='application/json')

    def test_registration_persists_hashed_password_and_logs_in(self):
        response = self.signup(is_staff=True, is_superuser=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['display_name'], '테스트 사용자')
        user = get_user_model().objects.get(username='new_member')
        self.assertEqual(user.first_name, '테스트 사용자')
        self.assertNotEqual(user.password, self.body['password'])
        self.assertTrue(check_password(self.body['password'], user.password))
        self.assertNotIn('password', response.json())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.date_joined)
        self.assertEqual(self.client.get('/api/v1/auth/session/').json()['display_name'], '테스트 사용자')
        self.assertEqual(self.client.get('/api/v1/agent/status/').json(), {'links': []})
        self.assertEqual(AgentLink.objects.count(), 0)
        self.assertEqual(self.signup().status_code, 409)
        self.client.post('/api/v1/auth/logout/')
        response = self.client.post('/api/v1/auth/login/', {'username': 'NEW_MEMBER', 'password': self.body['password']}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_registration_needs_csrf_and_rotates_session(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/v1/auth/signup/', self.body, content_type='application/json').status_code, 403)
        csrf = client.get('/api/v1/auth/session/').json()['csrf']
        old_cookie = client.cookies['csrftoken'].value
        response = client.post('/api/v1/auth/signup/', self.body, content_type='application/json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(client.cookies['csrftoken'].value, old_cookie)
        self.assertEqual(client.post('/api/v1/agent/pairing/', content_type='application/json', HTTP_X_CSRFTOKEN=csrf).status_code, 403)
        fresh = client.get('/api/v1/auth/session/').json()['csrf']
        self.assertEqual(client.post('/api/v1/agent/pairing/', content_type='application/json', HTTP_X_CSRFTOKEN=fresh).status_code, 201)

    def test_duplicates_are_case_insensitive_and_do_not_change_owner(self):
        original = get_user_model().objects.create_user('Existing', password='Original!password-4432')
        response = self.signup(username='EXISTING')
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json()['errors'])
        self.assertEqual(get_user_model().objects.count(), 1)
        original.refresh_from_db()
        self.assertTrue(original.check_password('Original!password-4432'))

    def test_invalid_passwords_and_confirmation_leave_no_account(self):
        for password in ['short', '1234567890123', 'password123', 'New_Member2026']:
            with self.subTest(password=password):
                response = self.signup(password=password, password_confirm=password)
                self.assertEqual(response.status_code, 400)
                self.assertIn('password', response.json()['errors'])
        self.assertIn('password_confirm', self.signup(password_confirm='different').json()['errors'])
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_invalid_types_reserved_names_and_lengths(self):
        for field, value in [('username', 'local-owner'), ('username', 'apple_reserved'), ('username', 'a'),
                             ('username', '<script>'), ('username', 'a' * 31), ('username', {}),
                             ('nickname', ['x']), ('nickname', 'x' * 31), ('password', {}), ('password', 'x' * 129)]:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.signup(**{field: value}).status_code, 400)
        for body in ['not json', '[]', 'null', '123']:
            self.assertEqual(self.client.post('/api/v1/auth/signup/', body, content_type='application/json').status_code, 400)
            self.assertEqual(self.client.post('/api/v1/auth/login/', body, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get('/api/v1/auth/signup/').status_code, 405)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_nickname_is_optional_and_other_accounts_are_isolated(self):
        response = self.signup(nickname='')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['display_name'], 'new_member')
        other = get_user_model().objects.create_user('other')
        AgentLink.objects.create(owner=other, token_hash='a' * 64)
        self.assertEqual(self.client.get('/api/v1/agent/status/').json()['links'], [])
