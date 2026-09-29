import random
import string

from django.test import Client, TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User


class UserNumberAnswersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()

        cls.random_suffix = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

        cls.username = 'test_john_%s'.lower() % cls.random_suffix
        cls.email = 'test_%s@email.com'.lower() % cls.random_suffix

        cls.register_payload = {
            'username': cls.username,
            'email': cls.email,
            'password': 'something_secret'
        }
        response = cls.client.post(
            reverse('api_register'), cls.register_payload
        )
        cls.token = response.json().get('token')
        cls.user_id = response.json().get('user_id')

        cls.another_user_x = User.objects.create(
            username='another_xuser_%s' % cls.random_suffix,
            email='another_xuser_%s@mail.com' % cls.random_suffix,
            is_active=True
        )

    def _assert_counts(self, counter, expected):
        profile = self.another_user_x.profile
        profile.update_number_answers(counter=counter)
        profile.refresh_from_db()
        self.assertEqual(profile.answers_this_week, expected)
        self.assertEqual(profile.answers_this_month, expected)
        self.assertEqual(profile.total_answers, expected)

    def test_number_answers_sequence(self):
        """
        Zähler hoch und runter in einem Test: TestCase setzt die DB nach jedem
        Test zurück, getrennte Test-Methoden können nicht aufeinander aufbauen.
        """
        self._assert_counts(1, 1)
        self._assert_counts(1, 2)
        self._assert_counts(0, 2)
        self._assert_counts(-1, 1)
        self._assert_counts(-1, 0)
        # darf nicht unter 0 fallen
        self._assert_counts(-1, 0)
