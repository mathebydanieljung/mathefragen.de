from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from websocket import create_connection

from mathefragen.apps.core.models import Base
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.messaging.models import Message
from mathefragen.apps.question.models import Question


class Review(Base):
    class Meta:
        db_table = 'user_review'

    RELATION_SOURCES = (
        ('helper', 'Hat mir geholfen'),
        ('worked_together', 'Zusammen gearbeitet'),
        ('studied_together', 'Zusammen studiert')
    )
    given_by = models.ForeignKey(
        User,
        related_name='given_reviews',
        on_delete=models.CASCADE
    )
    given_to = models.ForeignKey(
        User,
        related_name='received_reviews',
        on_delete=models.CASCADE
    )
    source_question = models.ForeignKey(
        Question,
        related_name='reviews_from_question',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField()
    relation_source = models.CharField(
        max_length=50,
        choices=RELATION_SOURCES,
        default='',
        blank=True
    )
    hashtags = models.ManyToManyField(
        HashTag,
        related_name='confirmed_hashtags',
        db_table='user_review_hashtags'
    )
    soft_deleted = models.BooleanField(default=False)

    def inform_about_review(self):
        if settings.ENABLE_WEBSOCKETS:
            msg = Message.objects.create(
                title='Neue Bewertung für dich',
                message='%s hat für dich eine Bewertung geschrieben.' % self.given_by.profile.username,
                link=self.given_to.profile.get_absolute_url(),
                type='Bewertung'
            )

            msg.to_users.add(self.given_to)
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % self.given_to_id)
                ws.send('Bewertung')
                ws.close()
            except Exception:
                pass

    @classmethod
    def copy(cls):
        for obj in cls.objects.all():
            r = UserReview.objects.create(
                given_by_id=obj.given_by_id,
                given_to_id=obj.given_to_id,
                source_question_id=obj.source_question_id,
                text=obj.text,
                relation_source=obj.relation_source,
                soft_deleted=obj.soft_deleted
            )
            for t in obj.hashtags.all():
                r.hashtags.add(t.id)

    def __str__(self):
        return self.text


class UserReview(Base):
    RELATION_SOURCES = (
        ('helper', 'Hat mir geholfen'),
        ('worked_together', 'Zusammen gearbeitet'),
        ('studied_together', 'Zusammen studiert')
    )
    given_by = models.ForeignKey(
        User,
        related_name='given_user_reviews',
        on_delete=models.CASCADE
    )
    given_to = models.ForeignKey(
        User,
        related_name='received_user_reviews',
        on_delete=models.CASCADE
    )
    source_question = models.ForeignKey(
        Question,
        related_name='user_reviews_from_question',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField()
    relation_source = models.CharField(
        max_length=50,
        choices=RELATION_SOURCES,
        default='',
        blank=True
    )
    hashtags = models.ManyToManyField(
        HashTag,
        related_name='user_review_hashtags'
    )
    soft_deleted = models.BooleanField(default=False)
    is_happy = models.BooleanField(default=False)

    def inform_about_review(self):
        if settings.ENABLE_WEBSOCKETS:
            msg = Message.objects.create(
                title='Neue Bewertung für dich',
                message='%s hat für dich eine Bewertung geschrieben.' % self.given_by.profile.username,
                link=self.given_to.profile.get_absolute_url(),
                type='Bewertung'
            )

            msg.to_users.add(self.given_to)
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % self.given_to_id)
                ws.send('Bewertung')
                ws.close()
            except Exception:
                pass

    def __str__(self):
        return self.text
