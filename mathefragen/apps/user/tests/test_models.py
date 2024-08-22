from django.test import TestCase
from django.contrib.auth.models import User


class UserModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='user1', email='user@email.com', is_active=True
        )

    def test_user(self):
        user = User.objects.get(username='user1')
        self.assertEqual(user, self.user)
        self.assertEqual(user.profile, self.user.profile)

