from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from mathefragen.apps.question.models import Question, Answer
from mathefragen.apps.playlist.models import Playlist


class GlobalStats(models.Model):
    total_questions = models.IntegerField(default=0)
    total_users = models.IntegerField(default=0)
    total_answers = models.IntegerField(default=0)
    percent_answered = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0.0
    )
    unanswered_questions = models.IntegerField(default=0)
    answered_questions = models.IntegerField(default=0)

    def update_total_questions(self):
        self.total_questions = Question.objects.filter(is_active=True).count()
        self.save()
        self.update_answered_questions()
        self.update_unanswered_questions()

    def update_total_users(self):
        self.total_users = User.objects.filter(is_staff=False).count()
        self.save()

    def update_total_answers(self):
        self.total_answers = Answer.objects.all().count()
        self.save()
        self.update_answered_questions()
        self.update_unanswered_questions()

    def update_answered_questions(self):
        self.answered_questions = Question.objects.filter(Q(number_answers__gte=1) | Q(closed=True)).count()
        self.save()
        self.update_percent_answered()

    def update_unanswered_questions(self):
        self.unanswered_questions = Question.objects.filter(number_answers=0).count()
        self.save()
        self.update_percent_answered()

    def update_percent_answered(self):
        if not self.total_questions:
            self.percent_answered = Decimal(0)
        else:
            # the bug decimal.InvalidOperation does not happen, because the first interaction is asking a question.
            # not answering one. So the stats is updated on time.
            percent_answered = self.answered_questions * 100 / self.total_questions
            if percent_answered:
                self.percent_answered = Decimal(percent_answered)
            else:
                self.percent_answered = Decimal(0)

        self.save(update_fields=['percent_answered'])


class QuestionView(models.Model):
    idate = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        User,
        related_name='user_question_views',
        on_delete=models.SET_NULL,
        null=True
    )
    question = models.ForeignKey(
        Question,
        related_name='question_views',
        on_delete=models.CASCADE
    )
    source_ip = models.GenericIPAddressField(default='192.168.0.1', db_index=True)

    def __str__(self):
        return 'views'


class PlaylistView(models.Model):
    idate = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        User,
        related_name='user_playlist_views',
        on_delete=models.SET_NULL,
        null=True
    )
    question = models.ForeignKey(
        Playlist,
        related_name='playlist_views',
        on_delete=models.CASCADE
    )
    source_ip = models.GenericIPAddressField(default='192.168.0.1', db_index=True)

    def __str__(self):
        return 'views'
