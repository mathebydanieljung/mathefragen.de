from django.db import models

from mathefragen.apps.core.models import Base
from mathefragen.apps.question.models import Question


class HashTag(Base):
    name = models.CharField(max_length=100)  # unique=True add this again
    questions = models.ManyToManyField(
        Question,
        related_name='question_hashtags',
        blank=True
    )
    is_main_tag = models.BooleanField(default=False, verbose_name='Haupt-Tag')
    subtags = models.ManyToManyField('self', blank=True, verbose_name='Sub-Tags')

    @property
    def number_of_usages(self):
        return self.questions.all().count() + self.playlist_set.all().count()

    def __str__(self):
        return self.name
