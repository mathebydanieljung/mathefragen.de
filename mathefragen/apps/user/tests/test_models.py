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


class ProfileAggregatesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        from mathefragen.apps.hashtag.models import HashTag
        from mathefragen.apps.question.models import Question, Answer

        cls.helper = User.objects.create(username='helper')
        cls.other = User.objects.create(username='other')
        cls.q1 = Question.objects.create(user=cls.other, title='q1', last_acted_user=cls.helper)
        cls.q2 = Question.objects.create(user=cls.other, title='q2', last_acted_user=cls.other,
                                         last_acted_user_username='other')
        Answer.objects.create(user=cls.helper, question=cls.q1, text='a')
        Answer.objects.create(user=cls.helper, question=cls.q1, text='b')
        Answer.objects.create(user=cls.helper, question=cls.q2, text='c')
        Answer.objects.create(user=cls.other, question=cls.q2, text='d')
        # same name in different case is merged, answering q1 twice counts once
        HashTag.objects.create(name='Analysis').questions.add(cls.q1)
        HashTag.objects.create(name='analysis').questions.add(cls.q2)
        HashTag.objects.create(name='geometrie').questions.add(cls.q1)

    def test_get_helper_ids_ranked_by_answer_count(self):
        from mathefragen.apps.user.models import Profile
        self.assertEqual(Profile.get_helper_ids(slice_number=2), [self.helper.id, self.other.id])
        self.assertEqual(Profile.get_helper_ids(slice_number=1), [self.helper.id])

    def test_most_helped_tags(self):
        self.assertEqual(self.helper.profile.retrieve_most_helped_tags(), 'analysis,geometrie')

    def test_speed_fields_only_touch_own_last_acted_questions(self):
        profile = self.helper.profile
        profile.update_question_speed_fields()
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.last_acted_user_username, 'helper')
        self.assertEqual(self.q1.last_acted_user_url, profile.get_absolute_url())

        profile.update_question_speed_fields(reset=True)
        self.q1.refresh_from_db()
        self.q2.refresh_from_db()
        self.assertEqual(self.q1.last_acted_user_username, '')
        # q2 was answered by helper but last acted on by another user: untouched
        self.assertEqual(self.q2.last_acted_user_username, 'other')
