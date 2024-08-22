import random
import string

from rest_framework import status

from django.test import Client, TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User

from mathefragen.apps.question.api.serializers import (
    AnswerSerializer, AnswerCommentSerializer
)
from .. models import Question, Answer, AnswerComment


class AnswerAPITestCase(TestCase):
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

        cls.another_user = User.objects.create(
            username='another_user_%s' % cls.random_suffix,
            email='another_user_%s@mail.com' % cls.random_suffix,
            is_active=True
        )

        cls.question = Question.objects.create(
            title='AnswerAPITest_title', text='AnswerAPITest_text', user_id=cls.user_id
        )
        cls.answer = Answer.objects.create(
            question_id=cls.question.id, text='AnswerAPITest_answer text', user_id=cls.user_id
        )
        cls.create_answer_payload = {
            'text': 'test_answer', 'user': cls.user_id
        }
        cls.create_answer_comment_payload = {
            'text': 'test_answer_comment', 'user': cls.user_id, 'answer_id': cls.answer.id
        }

    def test_answer_list(self):
        response = self.client.get(
            reverse('api_question_answers_list', kwargs={'question_id': self.question.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_all_answers_list(self):
        response = self.client.get('%s?user=%s' % (reverse('api_all_answers_list'), self.user_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get('%s?user=%s' % (reverse('api_all_answers_list'), self.another_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_answer_create(self):
        response = self.client.post(
            reverse('api_create_answer', kwargs={'question_id': self.question.id}),
            data=self.create_answer_payload,
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        answer = Answer.objects.get(text='test_answer')
        self.assertEqual(answer.text, 'test_answer')

    def test_answer_detail(self):
        response = self.client.get(
            reverse('api_answer_detail', kwargs={
                'question_id': self.question.id,
                'answer_id': self.answer.id
            })
        )
        serialized_data = AnswerSerializer(self.answer).data
        self.assertEqual(serialized_data, response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_answer_update(self):
        update_answer_payload = {
            'text': 'test_answer_updated',
            'question': self.question.id,
            'user': self.user_id,
            'id': self.answer.id
        }
        response = self.client.put(
            reverse('api_answer_put', kwargs={
                'question_id': self.question.id,
                'answer_id': self.answer.id
            }),
            data=update_answer_payload,
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.text, 'test_answer_updated')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_answer_update_accept(self):
        response = self.client.post(
            reverse('api_accept_answer', kwargs={
                'question_id': self.question.id,
                'answer_id': self.answer.id
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.accepted, True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_answer_delete(self):
        # delete answer
        response = self.client.delete(
            reverse('api_answer_delete', kwargs={
                'question_id': self.question.id,
                'answer_id': self.answer.id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        question_id = self.question.id
        answer_id = self.answer.id

        # test if object deleted
        response = self.client.get(
            reverse('api_answer_detail', kwargs={
                'question_id': question_id,
                'answer_id': answer_id
            }),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_answer_comment_create(self):
        response = self.client.post(
            reverse('api_create_answer_comment', kwargs={
                'answer_id': self.answer.id
            }),
            data=self.create_answer_comment_payload,
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_answer_comment_id = response.json().get('id')
        new_answer_comment = AnswerComment.objects.get(id=new_answer_comment_id)
        self.assertEqual(AnswerCommentSerializer(new_answer_comment).data, response.json())

    def test_answer_comment_list(self):
        AnswerComment.objects.create(
            answer=self.answer, user_id=self.user_id, text='main answer comment'
        )
        response = self.client.get(
            reverse('api_answer_comments_list', kwargs={
                'answer_id': self.answer.id
            })
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_answer_comment_update(self):
        answer_comment = AnswerComment.objects.create(
            answer=self.answer, user_id=self.user_id, text='main answer comment'
        )
        response = self.client.put(
            reverse('api_answer_comment_put', kwargs={
                'answer_id': self.answer.id,
                'comment_id': answer_comment.id
            }),
            data={'text': 'test_answer_comment_updated', 'user': self.user_id},
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        answer_comment.refresh_from_db()
        self.assertEqual(answer_comment.text, 'test_answer_comment_updated')

    def test_answer_comment_delete(self):
        answer_comment = AnswerComment.objects.create(
            answer=self.answer, user_id=self.user_id, text='main answer comment'
        )
        response = self.client.delete(
            reverse('api_answer_comment_delete', kwargs={
                'answer_id': self.answer.id,
                'comment_id': answer_comment.id
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
