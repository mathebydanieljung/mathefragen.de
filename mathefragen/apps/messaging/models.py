from django.contrib.auth.models import User
from django.db import models

from mathefragen.apps.core.models import Base


class Message(Base):
    title = models.CharField(max_length=300)
    link = models.TextField(default='', blank=True)
    message = models.TextField()
    from_user = models.ForeignKey(
        User,
        related_name='user_sent_msgs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    to_users = models.ManyToManyField(
        User,
        blank=True
    )
    to_all = models.BooleanField(null=True)
    type = models.CharField(max_length=100, blank=True, db_index=True)

    def __str__(self):
        return self.message


class ReadMessage(models.Model):
    idate = models.DateTimeField(auto_now_add=True, db_index=True)
    message = models.ForeignKey(
        Message,
        related_name='read_messages',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='user_read_messages',
        on_delete=models.CASCADE
    )
