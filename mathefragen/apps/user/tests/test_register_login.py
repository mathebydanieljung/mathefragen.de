import random
import string

from rest_framework import status

from django.test import Client, TestCase
from django.shortcuts import reverse


class RegisterLoginTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.random_suffix = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

        cls.username = 'test_john_%s' % cls.random_suffix
        cls.email = 'test_%s@email.com' % cls.random_suffix

        cls.register_payload = {
            'username': cls.username,
            'email': cls.email,
            'password': 'something_secret'
        }
        cls.social_register_payload = {
            'username': cls.username,
            'email': cls.email,
            'password': 'something_secret',
            'social_sign': 'facebook'
        }
        cls.username_login_payload = {
            'login_id': cls.username,
            'login_pwd': 'something_secret'
        }
        cls.email_login_payload = {
            'login_id': cls.email,
            'login_pwd': 'something_secret'
        }
        cls.headers = {
            'Content-Type': 'application/json'
        }
        cls.client = Client()

        response = cls.client.post(
            reverse('api_register'), cls.register_payload
        )
        cls.token = response.json().get('token')

    def test_a_register(self):
        copy_register_payload = self.register_payload.copy()
        copy_register_payload['username'] = '%s_copy' % copy_register_payload.get('username')

        response = self.client.post(
            reverse('api_register'), copy_register_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.json().keys())

        social_register_payload = self.social_register_payload.copy()
        social_register_payload['username'] = '%s_facebook' % social_register_payload.get('username')

        response = self.client.post(
            reverse('api_register'), social_register_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.json().keys())

        response = self.client.post(
            reverse('api_register'), social_register_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.json().keys())

    def test_a_register_with_invalid_email(self):
        copy_register_payload = self.register_payload.copy()
        copy_register_payload['username'] = '%s_copy' % copy_register_payload.get('username')
        copy_register_payload['email'] = '%s_copy' % copy_register_payload.get('email')

        response = self.client.post(
            reverse('api_register'), copy_register_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_register_login_with_capital_letters(self):
        copy_register_payload = self.register_payload.copy()
        copy_register_payload['username'] = 'Copy_%s' % copy_register_payload.get('username')
        copy_register_payload['email'] = 'Copy_%s' % copy_register_payload.get('email')

        response = self.client.post(
            reverse('api_register'), copy_register_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.json().keys())

        # login with capital letter
        copy_username_login_payload = self.username_login_payload.copy()
        copy_username_login_payload['login_id'] = self.register_payload.get('username')
        response = self.client.post(
            reverse('api_login_me'), copy_username_login_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json().keys())

        # login with small letter
        copy_username_login_payload = copy_username_login_payload.copy()
        copy_username_login_payload['login_id'] = copy_username_login_payload.get('login_id').lower()
        response = self.client.post(
            reverse('api_login_me'), copy_username_login_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json().keys())

    def test_b_user_login(self):
        # test login via username
        response = self.client.post(
            reverse('api_login_me'), self.username_login_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json().keys())

        # test login via email
        response = self.client.post(
            reverse('api_login_me'), self.email_login_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json().keys())

    def test_c_access_with_right_and_wrong_token(self):
        # test login via username
        response = self.client.post(
            reverse('api_login_me'), self.username_login_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json().keys())

        token = response.json().get('token')
        questions_list_url = reverse('api_questions_list')

        questions_list_response = self.client.get(
            questions_list_url, HTTP_AUTHORIZATION='JWT {}_wrong'.format(token)
        )
        self.assertEqual(questions_list_response.status_code, status.HTTP_401_UNAUTHORIZED)

        questions_list_response = self.client.get(
            questions_list_url, HTTP_AUTHORIZATION='JWT {}'.format(token)
        )
        self.assertEqual(questions_list_response.status_code, status.HTTP_200_OK)
