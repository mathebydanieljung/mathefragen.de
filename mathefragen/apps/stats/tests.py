import json

from django.test import Client, TestCase
from django.shortcuts import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from mathefragen.apps.question.models import (
    Question,
    Answer,
    QuestionComment,
    AnswerComment,
)
from mathefragen.apps.stats.models import GlobalStats


class DeeperStatsTestCase(TestCase):
    """
    Verifies the /v1/stats/numbers/deeper/ endpoint that powers the
    global stats modal (templates/modals/global_stats.html).
    """

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()

        cls.asker = User.objects.create(username='asker', email='asker@mail.com', is_active=True)
        cls.helper_a = User.objects.create(username='helper_a', email='a@mail.com', is_active=True)
        cls.helper_b = User.objects.create(username='helper_b', email='b@mail.com', is_active=True)

        # Two recent questions (within all ranges). q1 is the more upvoted one.
        cls.q1 = Question.objects.create(
            user=cls.asker, title='Frage 1', text='t1',
            number_answers=2, vote_points=10, views=100,
        )
        cls.q2 = Question.objects.create(
            user=cls.asker, title='Frage 2', text='t2',
            number_answers=1, vote_points=5, views=50,
        )
        # Unanswered + no votes -> counts toward total questions but not answered/top.
        cls.q3 = Question.objects.create(
            user=cls.asker, title='Frage 3', text='t3',
            number_answers=0, vote_points=0, views=5,
        )

        # helper_b is created last (higher id) but gives more answers, so it
        # must rank first. This guards against ranking by id instead of by
        # answer count.
        Answer.objects.create(user=cls.helper_a, question=cls.q1, text='a1')
        Answer.objects.create(user=cls.helper_b, question=cls.q2, text='a2')
        Answer.objects.create(user=cls.helper_b, question=cls.q1, text='a3')

        QuestionComment.objects.create(user=cls.asker, question=cls.q1, text='qc')
        AnswerComment.objects.create(
            user=cls.asker,
            answer=Answer.objects.first(),
            text='ac',
        )

    def _get(self, time_range):
        response = self.client.get(
            reverse('deeper_stats'), {'range': time_range}
        )
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def test_counts_within_30_day_range(self):
        payload = self._get('30')

        self.assertEqual(payload['questions_num'], 3)
        self.assertEqual(payload['answers_num'], 3)
        self.assertEqual(payload['comments_num'], 2)

        # 2 of 3 questions answered -> 66.x %
        self.assertGreater(payload['percentage_answers'], 60)
        self.assertLess(payload['percentage_answers'], 70)

    def test_top_questions_sorted_by_votes(self):
        payload = self._get('30')

        titles = [q['title'] for q in payload['top_3_questions']]
        self.assertEqual(titles, ['Frage 1', 'Frage 2'])
        self.assertEqual(payload['top_3_questions'][0]['views'], 100)
        self.assertEqual(payload['top_3_questions'][0]['answers'], 2)

    def test_top_helpers_sorted_by_answer_count(self):
        payload = self._get('30')

        usernames = [h['username'] for h in payload['top_3_helpers']]
        # helper_b (2 answers, higher id) must rank before helper_a (1 answer).
        self.assertEqual(usernames, ['helper_b', 'helper_a'])

    def test_range_filtering_excludes_old_records(self):
        old = timezone.now() - timezone.timedelta(days=400)
        # Backdate everything (auto_now_add can't be set at create time).
        Question.objects.update(idate=old)
        Answer.objects.update(idate=old)
        QuestionComment.objects.update(idate=old)
        AnswerComment.objects.update(idate=old)

        recent = self._get('30')
        self.assertEqual(recent['questions_num'], 0)
        self.assertEqual(recent['answers_num'], 0)
        self.assertEqual(recent['comments_num'], 0)
        self.assertEqual(recent['top_3_helpers'], [])
        self.assertEqual(recent['top_3_questions'], [])

        total = self._get('total')
        self.assertEqual(total['questions_num'], 3)
        self.assertEqual(total['answers_num'], 3)

    def test_inactive_questions_excluded_from_total(self):
        # An inactive question must not inflate the question count, just like
        # GlobalStats.total_questions (filter(is_active=True)).
        Question.objects.create(
            user=self.asker, title='inactive', text='x',
            number_answers=0, vote_points=0, is_active=False,
        )
        payload = self._get('total')
        self.assertEqual(payload['questions_num'], 3)

    def test_percentage_matches_index_page_globalstats(self):
        # The "Insgesamt" tab must agree with the answered-percentage shown on
        # the index page, which comes from GlobalStats. The mismatch report was
        # caused by an inactive-but-answered question: it is excluded from the
        # total yet still counts as answered (GlobalStats does the same).
        Question.objects.create(
            user=self.asker, title='inactive answered', text='x',
            number_answers=1, vote_points=0, is_active=False,
        )

        gs = GlobalStats.objects.create()
        gs.update_total_questions()
        gs.update_total_answers()
        gs.refresh_from_db()

        payload = self._get('total')
        self.assertEqual(payload['questions_num'], gs.total_questions)
        self.assertEqual(
            round(payload['percentage_answers'], 1), float(gs.percent_answered)
        )

    def test_empty_database_returns_zeroes(self):
        Question.objects.all().delete()
        Answer.objects.all().delete()
        QuestionComment.objects.all().delete()
        AnswerComment.objects.all().delete()

        payload = self._get('30')
        self.assertEqual(payload['questions_num'], 0)
        self.assertEqual(payload['percentage_answers'], 0)
        self.assertEqual(payload['top_3_helpers'], [])
