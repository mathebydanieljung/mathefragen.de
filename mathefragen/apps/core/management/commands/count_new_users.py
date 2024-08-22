from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from mathefragen.apps.question.models import Question, Answer, QuestionComment, AnswerComment


class Command(BaseCommand):

    def handle(self, *args, **options):
        this_time_yesterday = timezone.now() - timezone.timedelta(days=1)

        new_users_since_then = User.objects.filter(date_joined__gte=this_time_yesterday).count()
        new_questions_since_then = Question.objects.filter(idate__gte=this_time_yesterday).count()
        new_answers_since_then = Answer.objects.filter(idate__gte=this_time_yesterday).count()

        new_comments_since_then = QuestionComment.objects.filter(idate__gte=this_time_yesterday).count()
        new_comments_since_then += AnswerComment.objects.filter(idate__gte=this_time_yesterday).count()

        total_number_users = User.objects.count()
        total_number_questions = Question.objects.count()
        total_number_answers = Answer.objects.count()
        total_number_comments = QuestionComment.objects.count() + AnswerComment.objects.count()

        if new_users_since_then:
            send_mail(
                '%s Neue Nutzer seit gestern auf mathefragen.de' % new_users_since_then,

                'Seit gestern: \n\n'
                '%s neue Nutzer \n\n'
                '%s neue Fragen \n\n'
                '%s neue Antworten \n\n'
                '%s neue Kommentare \n\n'
                '-------------------------------\n\n'
                'Insgesamt: \n\n'
                '%s Nutzer \n\n'
                '%s Fragen \n\n'
                '%s Antworten \n\n'
                '%s Kommentare' %
                (
                    new_users_since_then,
                    new_questions_since_then,
                    new_answers_since_then,
                    new_comments_since_then,

                    total_number_users,
                    total_number_questions,
                    total_number_answers,
                    total_number_comments
                ),
                'no-reply@visionsfirst.de',
                settings.ADMINS_TO_REPORT,
            )
