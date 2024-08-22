from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from websocket import create_connection

from mathefragen.apps.core.models import Base
from mathefragen.apps.messaging.models import Message
from mathefragen.apps.playlist.models import Playlist
from mathefragen.apps.question.models import Question, Answer, AnswerComment, QuestionComment


class CommentVote(Base):
    answer_comment = models.ForeignKey(
        AnswerComment,
        related_name='answer_comment_votes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    question_comment = models.ForeignKey(
        QuestionComment,
        related_name='question_comment_votes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        related_name='user_comment_votes',
        on_delete=models.CASCADE,
        null=True
    )


class Vote(Base):
    VOTE_TYPES = (
        ('up', 'Up'),
        ('down', 'Down')
    )
    question = models.ForeignKey(
        Question,
        related_name='question_votes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    answer = models.ForeignKey(
        Answer,
        related_name='answer_votes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='playlist_votes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        related_name='user_votes',
        on_delete=models.CASCADE,
        null=True
    )
    type = models.CharField(max_length=5, choices=VOTE_TYPES, default='', blank=True, db_index=True)
    reason = models.TextField(default='', blank=True)

    def __str__(self):
        return '%s for %s' % (
            self.type, 'question [%s]' % self.question_id if self.question_id else 'answer [%s]' % self.answer_id
        )

    def inform_about_vote(self):
        if not settings.DEBUG:
            vote_type = 'upvote' if self.type == 'up' else 'downvote'

            if self.question_id:
                url = self.question.get_absolute_url()
                title = self.question.title
            elif self.answer_id:
                url = self.answer.question.get_absolute_url()
                title = self.answer.question.title
            else:
                url = self.playlist.get_absolute_url()
                title = self.playlist.name

            message = 'Du hast ein %s erhalten.' % vote_type.title()
            if 'down' in vote_type:
                message += ' Begründung: %s' % self.reason

            msg = Message.objects.create(
                title=title,
                message=message,
                link=url,
                type=vote_type
            )
            if self.question_id:
                given_to = self.question.user
            elif self.answer_id:
                given_to = self.answer.user
            else:
                given_to = self.playlist.user

            if given_to:
                # todo: sometimes there is no user. to be checked why.
                msg.to_users.add(given_to)

                if settings.ENABLE_WEBSOCKETS:
                    try:
                        ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % given_to.id)
                        ws.send(vote_type)
                        ws.close()
                    except Exception:
                        pass

    @classmethod
    def create_vote(cls, **kwargs):
        user = kwargs.get('user')
        answer = kwargs.get('answer')
        question = kwargs.get('question')
        playlist = kwargs.get('playlist')
        vote_type = kwargs.get('type')
        reason = kwargs.get('reason', '')

        created = False
        vote = None

        if question:
            if vote_type == 'up':

                # check if user already downvoted, if yes, we delete that downvote first
                if Vote.objects.filter(user_id=user.id, question_id=question.id, type='down').count():
                    Vote.objects.filter(user_id=user.id, question_id=question.id, type='down').delete()

                # upvote only if not upvoted yet
                if not Vote.objects.filter(user_id=user.id, question_id=question.id, type='up').count():
                    vote = Vote.objects.create(user_id=user.id, question_id=question.id, type='up')
                    created = True
            else:

                if not user.profile.can_down_vote():
                    # can't downvote because user is too new
                    return False

                # check if user already upvoted, if yes, we delete that upvote first
                if Vote.objects.filter(user_id=user.id, question_id=question.id, type='up').count():
                    Vote.objects.filter(user_id=user.id, question_id=question.id, type='up').delete()

                # down-vote only if not down-voted yet
                if not Vote.objects.filter(user_id=user.id, question_id=question.id, type='down').count():
                    vote = Vote.objects.create(user_id=user.id, question_id=question.id, type='down', reason=reason)
                    created = True

            if created:
                vote.inform_about_vote()

            return created

        elif playlist:
            if vote_type == 'up':
                # check if user already downvoted, if yes, we delete that downvote first
                if Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='down').count():
                    Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='down').delete()

                # upvote only if not upvoted yet
                if not Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='up').count():
                    vote = Vote.objects.create(user_id=user.id, playlist_id=playlist.id, type='up')
                    created = True
            else:

                if not user.profile.can_down_vote():
                    # can't downvote because user is too new
                    return False

                # check if user already upvoted, if yes, we delete that upvote first
                if Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='up').count():
                    Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='up').delete()

                # down-vote only if not down-voted yet
                if not Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='down').count():
                    vote = Vote.objects.create(user_id=user.id, playlist_id=playlist.id, type='down', reason=reason)
                    created = True

            if created:
                vote.inform_about_vote()

            return created

        elif answer:
            if vote_type == 'up':
                # check if user already downvoted, if yes, we delete that downvote first
                if Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='down').count():
                    Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='down').delete()

                # upvote only if not upvoted yet
                if not Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='up').count():
                    vote = Vote.objects.create(user_id=user.id, answer_id=answer.id, type='up')
                    created = True
            else:

                if not user.profile.can_down_vote():
                    # can't downvote because user is too new
                    return False

                # check if user already upvoted, if yes, we delete that upvote first
                if Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='up').count():
                    Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='up').delete()

                # down-vote only if not down-voted yet
                if not Vote.objects.filter(user_id=user.id, answer_id=answer.id, type='down').count():
                    vote = Vote.objects.create(user_id=user.id, answer_id=answer.id, type='down', reason=reason)
                    created = True

            if created:
                vote.inform_about_vote()

            return created
