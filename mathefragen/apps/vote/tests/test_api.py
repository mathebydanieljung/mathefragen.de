import random
import string

from rest_framework import status

from django.test import TestCase, Client
from django.shortcuts import reverse

from mathefragen.apps.question.models import Question, Answer


class VotesAPITestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()

        cls.random_suffix = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

        cls.username = 'test_voter_%s'.lower() % cls.random_suffix
        cls.email = 'voter_%s@email.com'.lower() % cls.random_suffix

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

        cls.question = Question.objects.create(
            title='Question to be voted', text='Question to be voted', user_id=cls.user_id
        )
        cls.answer = Answer.objects.create(
            question_id=cls.question.id, text='answer to be voted', user_id=cls.user_id
        )

    def test_question_vote(self):
        response = self.client.post(
            reverse('api_vote_question', kwargs={'question_id': self.question.id}), data={
                'type': 'up',
                'user': self.user_id,
                'question': self.question.id
            },
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        votes_url = reverse('api_votes_list')
        response = self.client.get(votes_url)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0].get('question'), self.question.id)

        votes_url = '%s?user=%s' % (reverse('api_votes_list'), self.user_id)
        response = self.client.get(votes_url)
        self.assertEqual(len(response.json()), 1)

        votes_url = '%s?question=%s' % (reverse('api_votes_list'), self.question.id)
        response = self.client.get(votes_url)
        self.assertEqual(len(response.json()), 1)

    def test_answer_vote(self):
        response = self.client.post(
            reverse('api_vote_answer', kwargs={
                'answer_id': self.answer.id
            }), data={
                'type': 'up',
                'user': self.user_id,
                'answer': self.answer.id
            },
            HTTP_AUTHORIZATION='JWT {}'.format(self.token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        votes_url = reverse('api_votes_list')
        response = self.client.get(votes_url)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0].get('answer'), self.answer.id)

        votes_url = '%s?user=%s' % (reverse('api_votes_list'), self.user_id)
        response = self.client.get(votes_url)
        self.assertEqual(len(response.json()), 1)

        votes_url = '%s?answer=%s' % (reverse('api_votes_list'), self.answer.id)
        response = self.client.get(votes_url)
        self.assertEqual(len(response.json()), 1)

