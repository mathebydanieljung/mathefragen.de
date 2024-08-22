from rest_framework import status

from django.test import TestCase, Client
from django.shortcuts import reverse
from django.contrib.auth.models import User

from mathefragen.apps.question.models import Question


class TestSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()

        cls.search_user = User.objects.create(
            username='search_user', email='search_user@mail.com', is_active=True
        )
        cls.question_1 = Question.objects.create(
            title='Lineare Algebra 1', text='Vektoren', user_id=cls.search_user.id
        )
        cls.question_2 = Question.objects.create(
            title='Lineare Algebra 2', text='Matrizen', user_id=cls.search_user.id
        )

    def test_search_question_api(self):
        search_term = 'Algebra'
        search_url = '%s?q=%s&type=question' % (reverse('api_search'), search_term)
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        found_questions = response.json().get('results')

        found = False
        for fq in found_questions:
            if search_term in fq.get('title') or search_term in fq.get('text'):
                found = True

        self.assertEqual(found, True)
        self.assertEqual(len(found_questions), 2)

        search_term = 'Vektoren'
        search_url = '%s?q=%s&type=question' % (reverse('api_search'), search_term)
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        found_questions = response.json().get('results')

        found = False
        for fq in found_questions:
            if search_term in fq.get('title') or search_term in fq.get('text'):
                found = True

        self.assertEqual(found, True)
        self.assertEqual(len(found_questions), 1)
        
    def test_search_user_api(self):
        search_term = 'search_user'
        search_url = '%s?q=%s&type=user' % (reverse('api_search'), search_term)
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        found_users = response.json().get('results')

        found = False
        for fu in found_users:
            if search_term in fu.get('username'):
                found = True

        self.assertEqual(found, True)
        self.assertEqual(len(found_users), 1)



