import random
import string

from rest_framework import status

from django.test import Client, TestCase
from django.shortcuts import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from mathefragen.apps.question.api.serializers import (
    QuestionSerializer, QuestionCommentSerializer
)
from .. models import Question, Answer, QuestionComment


class QuestionAPITestCase(TestCase):

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

        cls.just_another_used = User.objects.create(
            username='just_another_used', email='just_another_used@mail.com', is_active=True
        )

        cls.question = Question.objects.create(
            title='QuestionAPITest_title',
            text='QuestionAPITest_text  <strong>markdown strong</strong> <img src="../../media/img.url">',
            user_id=cls.user_id
        )
        cls.question_1 = Question.objects.create(
            title='QuestionAPITest_title_1_no_answer', text='QuestionAPITest_text', user_id=cls.user_id
        )
        cls.question_2 = Question.objects.create(
            title='QuestionAPITest_title_2_no_answer', text='QuestionAPITest_text', user_id=cls.user_id
        )
        cls.unanswered_question = Question.objects.create(
            title='QuestionAPITest_title_no_answer', text='QuestionAPITest_text', user_id=cls.just_another_used.id
        )

        cls.old_question = Question.objects.create(
            title='QuestionAPITest_title_old_question',
            text='QuestionAPITest_text  <strong>markdown strong</strong> <img src="../../media/img.url">',
            user_id=cls.user_id,
            idate=(timezone.now() - timezone.timedelta(hours=30))
        )
        cls.answer = Answer.objects.create(
            question_id=cls.question.id, text='main answer', user_id=cls.user_id
        )
        cls.comment = QuestionComment.objects.create(
            question_id=cls.question.id, user_id=cls.user_id, text='main question comment'
        )
        cls.create_comment_payload = {
            'text': 'comment 1', 'user': cls.user_id
        }

    def test_create_question(self):
        response = self.client.post(reverse('api_create_question'), data={
            'title': 'QuestionAPITest_title1',
            'text': 'QuestionAPITest_text1 <strong>markdown strong</strong> <img src="../../media/img.url">',
            'user': self.user_id,
            'anonymous': True,
            'hashtags': ['lala', 'lolo']
        }, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        question = Question.objects.get(title='QuestionAPITest_title1')
        # QuestionSerializer(question).data
        self.assertEqual(question.anonymous, True)

    def test_question_detail(self):
        response = self.client.get(
            reverse('api_question_detail', kwargs={'question_id': self.question.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_questions_list(self):
        response = self.client.get(reverse('api_questions_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_question_update(self):
        response = self.client.put(reverse('api_question_put', kwargs={'question_id': self.question.id}), data={
            'title': 'QuestionAPITest_title_updated', 'text': 'QuestionAPITest_text_updated', 'user': self.user_id
        }, content_type='application/json', HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, 'QuestionAPITest_title_updated')

    def test_question_delete(self):
        response = self.client.delete(
            reverse('api_question_delete', kwargs={'question_id': self.question.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # test if object deleted
        response = self.client.get(
            reverse('api_question_detail', kwargs={'question_id': self.question.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_create(self):
        response = self.client.post(
            reverse('api_create_question_comment', kwargs={
                'question_id': self.question.id
            }),
            data=self.create_comment_payload,
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        question = QuestionComment.objects.get(text='comment 1')
        serialized_data = QuestionCommentSerializer(question).data
        self.assertEqual(serialized_data, response.json())

    def test_comment_detail(self):
        response = self.client.get(
            reverse('api_question_comment_detail', kwargs={
                'question_id': self.question.id,
                'comment_id': self.comment.id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        serialized_data = QuestionCommentSerializer(self.comment).data
        self.assertEqual(serialized_data, response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_comment_list(self):
        response = self.client.get(
            reverse('api_question_comments_list', kwargs={
                'question_id': self.question.id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_comment_update(self):
        update_comment_payload = {
            'text': 'comment 2 updated',
            'question': self.question.id,
            'user': self.user_id,
            'id': self.comment.id
        }
        response = self.client.put(
            reverse('api_question_comment_put', kwargs={
                'question_id': self.question.id,
                'comment_id': self.comment.id
            }),
            data=update_comment_payload,
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, 'comment 2 updated')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment(self):
        response = self.client.delete(
            reverse('api_question_comment_delete', kwargs={
                'question_id': self.question.id,
                'comment_id': self.comment.id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # test if object deleted
        response = self.client.get(
            reverse('api_question_comment_detail', kwargs={
                'question_id': self.question.id,
                'comment_id': self.comment.id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_questions_filter_unanswered(self):
        filter_url = '%s?type=unanswered' % reverse('api_questions_list')
        response = self.client.get(filter_url, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_questions_filter_answered(self):
        filter_url = '%s?type=answered' % reverse('api_questions_list')
        response = self.client.get(filter_url, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('results')), 1)

    def test_questions_filter_new(self):
        filter_url = '%s?type=new' % reverse('api_questions_list')
        response = self.client.get(filter_url, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_questions_filter_user(self):
        filter_url = '%s?user=%s' % (reverse('api_questions_list'), self.user_id)
        response = self.client.get(filter_url, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_questions_filter_cut(self):
        filter_url = '%s?cut=1' % reverse('api_questions_list')
        response = self.client.get(filter_url, HTTP_AUTHORIZATION='JWT {}'.format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('results')), 1)




