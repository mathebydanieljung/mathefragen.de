from django.db import models
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base
from mathefragen.apps.question.models import Question
from mathefragen.apps.hashtag.models import HashTag


class UserFollow(Base):
    follower = models.ForeignKey(
        User,
        related_name='following_users',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return '%s follows %s' % (self.follower, self.following)


class QuestionFollow(Base):
    follower = models.ForeignKey(
        User,
        related_name='following_questions',
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        related_name='question_followers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('follower', 'question')

    def __str__(self):
        return '%s follows %s' % (self.follower, self.question)


class HashTagFollow(Base):
    follower = models.ForeignKey(
        User,
        related_name='following_hashtags',
        on_delete=models.CASCADE
    )
    hashtag = models.ForeignKey(
        HashTag,
        related_name='hashtag_followers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('follower', 'hashtag')

    def __str__(self):
        return '%s follows %s' % (self.follower, self.hashtag)
