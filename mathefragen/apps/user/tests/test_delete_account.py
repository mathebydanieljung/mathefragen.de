from rest_framework import status

from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import TestCase

from mathefragen.apps.user.models import GHOST_USERNAME
from mathefragen.apps.question.models import (
    Question, Answer, AnswerComment, QuestionComment
)


class SelfDeleteWebViewTestCase(TestCase):
    """Eingeloggter User löscht sein Konto über das Profil; Fragen/Antworten/
    Kommentare werden auf den geteilten ``mathghost``-User umgehängt."""

    def setUp(self):
        self.user = User.objects.create(
            username='to_be_deleted', email='bye@email.com', is_active=True
        )
        self.user.set_password('something_secret')
        self.user.save()

        self.question = Question.objects.create(
            title='Meine Frage', text='Meine Frage', user_id=self.user.id
        )
        self.answer = Answer.objects.create(
            question_id=self.question.id, text='Meine Antwort', user_id=self.user.id
        )
        self.answer_comment = AnswerComment.objects.create(
            answer_id=self.answer.id, text='Mein Antwort-Kommentar', user_id=self.user.id
        )
        self.question_comment = QuestionComment.objects.create(
            question_id=self.question.id, text='Mein Frage-Kommentar', user_id=self.user.id
        )

    def test_self_delete_reassigns_content_to_mathghost(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('delete_my_account'))
        self.assertEqual(response.status_code, 302)

        # account is gone
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

        # ghost collector exists and owns the content
        ghost = User.objects.get(username=GHOST_USERNAME)
        self.question.refresh_from_db()
        self.answer.refresh_from_db()
        self.answer_comment.refresh_from_db()
        self.question_comment.refresh_from_db()

        self.assertEqual(self.question.user_id, ghost.id)
        self.assertEqual(self.answer.user_id, ghost.id)
        self.assertEqual(self.answer_comment.user_id, ghost.id)
        self.assertEqual(self.question_comment.user_id, ghost.id)

        # personal IP trace removed from reassigned content
        self.assertEqual(self.answer.source_ip, '192.168.0.1')

    def test_delete_account_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('delete_my_account'))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_settings_page_renders_delete_modal(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('profile_settings', kwargs={'pk': self.user.id})
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('delete_account_modal', content)
        self.assertIn('confirm_delete_account', content)
        # confirmation is gated on typing the own username
        self.assertIn('data-username="%s"' % self.user.username, content)


class ApiDeleteOwnershipTestCase(TestCase):
    """Die API darf nur das eigene Konto löschen, nicht fremde."""

    def setUp(self):
        self.user = User.objects.create(
            username='api_self', email='self@email.com', is_active=True
        )
        self.user.set_password('something_secret')
        self.user.save()
        self.other = User.objects.create(
            username='api_other', email='other@email.com', is_active=True
        )

        token_response = self.client.post(
            reverse('api_login_me'),
            {'login_id': self.user.username, 'login_pwd': 'something_secret'},
        )
        self.token = token_response.json().get('token')

    def test_cannot_delete_other_user(self):
        response = self.client.delete(
            reverse('api_user_detail_delete', kwargs={'pk': self.other.id}),
            HTTP_AUTHORIZATION='JWT {}'.format(self.token),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())
