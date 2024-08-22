import datetime

from rest_framework import status

from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.test import Client, TestCase

from mathefragen.apps.user.api.serializers import ProfileSerializer
from mathefragen.apps.question.models import Question, Answer
from mathefragen.apps.user.models import Institution


class UserAPITestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.user = User.objects.create(
            username='user_test', email='user_test@email.com', is_active=True
        )
        cls.user.set_password(raw_password='something_secret')
        cls.user.save()

        cls.username_login_payload = {
            'login_id': cls.user.username,
            'login_pwd': 'something_secret'
        }
        response = cls.client.post(
            reverse('api_login_me'), cls.username_login_payload
        )
        cls.token = "%s" % response.json().get('token')

        cls.user1 = User.objects.create(
            username='user_test1', email='user_test1@email.com', is_active=True
        )
        cls.user2 = User.objects.create(
            username='user_test2', email='user_test2@email.com', is_active=True
        )
        cls.user3 = User.objects.create(
            username='user_test3', email='user_test3@email.com', is_active=True
        )
        cls.question = Question.objects.create(
            title='Question to be voted', text='Question to be voted', user_id=cls.user1.id
        )
        cls.answer = Answer.objects.create(
            question_id=cls.question.id, text='answer to be voted', user_id=cls.user2.id
        )
        cls.answer2 = Answer.objects.create(
            question_id=cls.question.id, text='answer2 for top helper test', user_id=cls.user2.id
        )
        cls.answer3 = Answer.objects.create(
            question_id=cls.question.id, text='answer3 for top helper test', user_id=cls.user1.id
        )
        cls.institution = Institution.objects.create(
            type='uni', name='LMU München'
        )

    def test_user_list(self):
        response = self.client.get(
            reverse('api_users_list'),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serialized_data = ProfileSerializer(self.user.profile).data
        self.assertIn(serialized_data, response.json().get('results'))

    def test_users_search(self):
        response = self.client.get(
            '%s?username=user_test1' % reverse('api_users_list'),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('results')), 1)

    def test_user_detail(self):
        response = self.client.get(
            reverse('api_user_detail_get', kwargs={'pk': self.user.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        serialized_data = ProfileSerializer(self.user.profile).data
        self.assertEqual(serialized_data, response.json())

    def test_user_delete(self):
        response = self.client.delete(
            reverse('api_user_detail_delete', kwargs={'pk': self.user.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # test if object deleted
        response = self.client.get(
            reverse('api_user_detail_get', kwargs={'pk': self.user.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_update_1(self):
        payload = {
            'bio_text': 'this is me, the human',
            'email': 'some_new_email@gmail.com',
            'username': 'username_updated',
            'first_name': 'changed_first_name',
            'last_name': 'changed_last_name',
            'status': 'student'
        }
        self.client.post(
            reverse('api_profile_change', kwargs={'pk': self.user.id}),
            data=payload,
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )

        profile = self.user.profile
        profile.refresh_from_db()

        self.assertEqual(profile.bio_text, 'this is me, the human')
        self.assertEqual(profile.user.email, 'some_new_email@gmail.com')
        self.assertEqual(profile.user.username, 'username_updated')
        self.assertEqual(profile.user.last_name, 'changed_last_name')
        self.assertEqual(profile.user.first_name, 'changed_first_name')
        self.assertEqual(profile.status, 'student')

    def test_top_helper(self):

        begin_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=2)).timestamp())
        end_timestamp = int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())

        response = self.client.get(
            '%s?begin=%s&end=%s' % (
                reverse('api_top_helper'), begin_timestamp, end_timestamp
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0].get('user_id'), self.user2.id)

