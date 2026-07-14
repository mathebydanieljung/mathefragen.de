from django.test import Client, TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User

from mathefragen.apps.user.models import Badge
from mathefragen.apps.stats.models import GlobalStats
from ..models import Question


class ToggleVisibilityTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='owner', email='owner@mail.com')
        cls.normal = User.objects.create(username='normal', email='normal@mail.com')
        cls.staff = User.objects.create(username='staff', email='staff@mail.com')
        cls.staff.is_staff = True
        cls.staff.save()

    def setUp(self):
        self.client = Client()
        self.question = Question.objects.create(
            title='Test', text='Test', user_id=self.owner.id, is_active=True
        )

    def _url(self):
        return reverse('toggle_question_visibility', kwargs={'question_id': self.question.id})

    def test_staff_toggles_visibility_off_then_on(self):
        self.client.force_login(self.staff)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_active)

        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_active)

    def test_normal_user_cannot_toggle_visibility(self):
        self.client.force_login(self.normal)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_active)


class DeleteQuestionAuthTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='del_owner', email='del_owner@mail.com')
        cls.staff = User.objects.create(username='del_staff', email='del_staff@mail.com')
        cls.staff.is_staff = True
        cls.staff.save()
        cls.other = User.objects.create(username='del_other', email='del_other@mail.com')

    def setUp(self):
        self.client = Client()
        # delete_question ruft request.stats.update_total_questions();
        # die AccountCheckMiddleware setzt request.stats = GlobalStats.objects.last().
        # Ohne Row waere request.stats None -> AttributeError.
        GlobalStats.objects.create()
        self.question = Question.objects.create(
            title='ToDelete', text='ToDelete', user_id=self.owner.id
        )

    def _url(self):
        return reverse('delete_question', kwargs={'question_id': self.question.id})

    def test_staff_admin_can_soft_delete(self):
        self.client.force_login(self.staff)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertTrue(self.question.soft_deleted)

    def test_unrelated_normal_user_cannot_delete(self):
        self.client.force_login(self.other)
        self.client.get(self._url())
        self.question.refresh_from_db()
        self.assertFalse(self.question.soft_deleted)
