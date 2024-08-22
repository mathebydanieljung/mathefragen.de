from django.db import models
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base


class QuestionTip(Base):
    author = models.ForeignKey(
        User,
        related_name='user_question_tips',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField(verbose_name='Tip Text')
    weight = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class HelpTip(Base):
    author = models.ForeignKey(
        User,
        related_name='user_helper_tips',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField(verbose_name='Tip Text')
    weight = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class PromotionBanner(Base):
    text = models.TextField(default='')
    link = models.TextField()

    background_color = models.CharField(max_length=10, default='#fff')
    text_color = models.CharField(max_length=10, default='#000')
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.text
