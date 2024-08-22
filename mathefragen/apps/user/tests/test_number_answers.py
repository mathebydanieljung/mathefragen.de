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

    def test_work_if_user_gives_answers(self):
        self.another_user_x.profile.update_number_answers(counter=1)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 1)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 1)
        self.assertEqual(self.another_user_x.profile.total_answers, 1)

    def test_work_if_user_gives_answers_again(self):
        self.another_user_x.profile.update_number_answers(counter=1)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 2)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 2)
        self.assertEqual(self.another_user_x.profile.total_answers, 2)

    def test_works_if_user_removes_answer(self):
        self.another_user_x.profile.update_number_answers(counter=-1)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 1)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 1)
        self.assertEqual(self.another_user_x.profile.total_answers, 1)

    def test_works_if_user_removes_answer_again(self):
        self.another_user_x.profile.update_number_answers(counter=-1)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 0)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 0)
        self.assertEqual(self.another_user_x.profile.total_answers, 0)

    def test_works_if_user_removes_answer_again_again(self):
        self.another_user_x.profile.update_number_answers(counter=-1)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 0)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 0)
        self.assertEqual(self.another_user_x.profile.total_answers, 0)

    def test_works_if_update_weekly_stats(self):
        self.another_user_x.profile.update_number_answers(counter=0)
        self.another_user_x.profile.refresh_from_db()
        self.assertEqual(self.another_user_x.profile.answers_this_week, 2)
        self.assertEqual(self.another_user_x.profile.answers_this_month, 2)
        self.assertEqual(self.another_user_x.profile.total_answers, 2)
