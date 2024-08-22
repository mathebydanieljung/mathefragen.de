from django.core.management.base import BaseCommand
from django.utils import timezone

from mathefragen.apps.question.models import Question


class Command(BaseCommand):

    def handle(self, *args, **options):
        now = timezone.now()
        open_questions = Question.objects.filter(
            number_answers=0, closed=False, rank_date__gte=(now - timezone.timedelta(hours=12))
        )
        for question in open_questions:
            if question.rank_date == (now - timezone.timedelta(hours=1)):
                question.re_rank(
                    reason='gefragt [2.Chance]',
                    repopulate=False
                )
            elif question.rank_date == (now - timezone.timedelta(hours=6)):
                question.re_rank(
                    reason='gefragt [3.Chance]',
                    repopulate=False
                )
            elif question.rank_date == (now - timezone.timedelta(hours=12)):
                question.re_rank(
                    reason='gefragt [4.Chance]',
                    repopulate=False
                )
