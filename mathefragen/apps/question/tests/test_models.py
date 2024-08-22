from django.test import TestCase
from django.contrib.auth.models import User

from .. models import Question


class UserTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='question_user', email='question_user@email.com', is_active=True
        )
        self.question = Question.objects.create(
            title='question title', text='question text', user=self.user
        )

    def test_user(self):
        question = Question.objects.get(title='question title')
        self.assertEqual(question, self.question)
        self.assertEqual(question.user, self.user)
