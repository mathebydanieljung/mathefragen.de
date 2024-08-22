from django.db import models
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base


class LearnToolSuggestion(Base):
    TYPES = (
        ('youtube', 'Youtube Channel'),
        ('app', 'App'),
        ('website', 'Webseite'),
        ('book', 'Buch')
    )
    type = models.CharField(
        choices=TYPES,
        default='',
        max_length=20
    )
    user = models.ForeignKey(
        User,
        related_name='learntool_suggestions',
        on_delete=models.CASCADE
    )
    description = models.TextField()

    def __str__(self):
        return self.description
