from django.test import TestCase
from django.contrib.auth.models import User

from mathefragen.apps.user.models import Badge


class CanModerateTestCase(TestCase):

    def test_normal_user_cannot_moderate(self):
        user = User.objects.create(username='normalo', email='normalo@mail.com')
        self.assertFalse(user.profile.can_moderate())

    def test_staff_user_can_moderate(self):
        user = User.objects.create(username='staffie', email='staffie@mail.com')
        user.is_staff = True
        user.save()
        self.assertTrue(user.profile.can_moderate())

    def test_badge_moderator_can_moderate(self):
        user = User.objects.create(username='modmod', email='modmod@mail.com')
        badge = Badge.objects.create(name='mod', can_edit_questions=True)
        user.profile.badges.add(badge)
        self.assertTrue(user.profile.can_moderate())
