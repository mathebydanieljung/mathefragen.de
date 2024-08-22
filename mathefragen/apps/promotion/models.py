from django.db import models
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base


class RightPromotion(Base):
    author = models.ForeignKey(
        User,
        related_name='user_right_promotions',
        on_delete=models.SET_NULL,
        null=True
    )
    link = models.TextField(default='', blank=True)
    text = models.TextField()

    def __str__(self):
        return self.text

