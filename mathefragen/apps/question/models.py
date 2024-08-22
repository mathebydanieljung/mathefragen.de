import hashlib
import json
import logging
import re
import statistics

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.text import slugify
from pyfcm import FCMNotification
from websocket import create_connection

from mathefragen.apps.core.models import Base
from mathefragen.apps.core.utils import send_email_in_template, RepairImages
from mathefragen.apps.guardian.tools.ip import IP
from mathefragen.apps.messaging.models import Message

logger = logging.getLogger(__name__)


class Category(Base):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Question(Base):
    TYPES = (
        ('question', 'Question'),
        ('article', 'Article')
    )
    user = models.ForeignKey(
        User,
        related_name='user_questions',
        on_delete=models.SET_NULL,
        null=True
    )
    followers = models.ManyToManyField(
        User,
        related_name='followed_questions'
    )
    title = models.CharField(max_length=200, db_index=True)
    text = models.TextField(default='')
    type = models.CharField(max_length=20, choices=TYPES, default='question')
    points = models.IntegerField(default=0, blank=True)
    views = models.IntegerField(default=0)
    device = models.CharField(max_length=200, default='')
    anonymous = models.BooleanField(default=False)
    closed = models.BooleanField(default=False, db_index=True)
    confirmed = models.BooleanField(default=True, db_index=True)
    vote_points = models.IntegerField(default=0, blank=True)
    number_answers = models.IntegerField(default=0, blank=True, db_index=True)
    number_tutor_pings = models.IntegerField(default=0, blank=True)
    solved_with_tutor = models.ForeignKey(
        User,
        related_name='helped_questions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    answerer = models.ForeignKey(
        User,
        related_name='answered_questions',
        null=True,
        on_delete=models.SET_NULL,
        blank=True
    )

    # just to re-rank the questions in index page
    rank_date = models.DateTimeField(null=True, db_index=True)
    rank_reason = models.CharField(max_length=100, default='')
    last_acted_user = models.ForeignKey(
        User,
        related_name='last_acted_questions',
        null=True,
        on_delete=models.SET_NULL
    )
    edited_by = models.ForeignKey(
        User,
        related_name='edited_questions',
        null=True,
        on_delete=models.SET_NULL
    )
    edited_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    is_first_question = models.BooleanField(default=False)

    soft_deleted = models.BooleanField(default=False)
    soft_deleted_at = models.DateTimeField(null=True, blank=True)

    # fields for the sake of speed
    tag_names = models.CharField(max_length=1024, default='', blank=True)
    last_acted_user_username = models.CharField(max_length=1024, default='', blank=True)
    last_acted_user_url = models.CharField(max_length=1024, default='', blank=True)
    last_acted_user_verified = models.BooleanField(default=False)

    # stats
    source_ip = models.GenericIPAddressField(default='192.168.0.1')

    @classmethod
    def answer_time_stats(cls, fast=False, long=False):
        answered_minutes = list()
        answered_questions = cls.objects.filter(number_answers__gt=0)
        for q in answered_questions:
            answers = q.question_answers.order_by('idate')
            if not answers:
                continue

            first_answer = answers[0]
            min_difference = abs((q.idate - first_answer.idate).total_seconds() // 60)
            answered_minutes.append(min_difference)

        if fast:
            return min(answered_minutes)

        if long:
            return max(answered_minutes)

        return statistics.mean(answered_minutes)

    def hard_delete(self):
        super(Question, self).delete()

    def delete(self, using=None, keep_parents=False):
        if self.user_id and self.user.profile.total_questions >= 1:
            self.user.profile.total_questions -= 1
            self.user.profile.save()

        self.soft_deleted = True
        self.closed = True
        self.soft_deleted_at = timezone.now()
        self.save()

    def can_be_deleted(self):
        """
        Question can not be deleted if following points are true:
        1. it has an answer with upvotes
        2. has an accepted answer
        3. has multiple answers
        todo: 4. has at least one other question that is marked as duplicate of this question
        5. not reached 5 deletions of own posts per day.

        Question can be deleted if:
        1. it has no Answer so far.

        if the owner is mod, he can delete his posts anytime.
        """
        # if no user anymore, then we keep the question. okay?
        if not self.user_id:
            return False

        if self.user.profile.is_moderator():
            return True

        if self.question_answers.count():
            return False

        if self.question_comments.count():
            return False

        voted_answers = self.question_answers.filter(vote_points__gt=0).count()
        accepted_answers = self.question_answers.filter(accepted=True).count()
        # deletions_today = self.user.user_questions.filter(soft_deleted_at__date=timezone.now().date()).count()

        if voted_answers:
            return False

        if accepted_answers:
            return False

        return True

    def can_be_edited(self):
        number_answers = self.question_answers.count()
        number_comments = self.question_comments.count()

        if number_answers:
            return False

        if number_comments:
            return False

        # question is not fully editable anymore after 24 hours.
        return self.idate > (timezone.now() - timezone.timedelta(hours=24))

    def go_online(self, user):
        """
        this is called when question is created without user first,
        then user registers -> question goes online
        """
        self.user_id = user.id
        self.is_active = True
        self.confirmed = True
        self.idate = timezone.now()

        if not user.profile.number_asks:
            self.is_first_question = True
        self.save()

        self.re_rank(reason='gefragt', last_acted_user=user)

        user.profile.number_asks += 1
        user.profile.total_questions = user.user_questions.filter(type='question').count()
        user.profile.save()

    def populate_speed_fields(self, only_user=False, reset=False):
        self.refresh_from_db(fields=['last_acted_user'])

        fields_to_update = ['last_acted_user_username', 'last_acted_user_url', 'last_acted_user_verified']

        if reset:
            self.last_acted_user_username = ''
            self.last_acted_user_url = ''
            self.last_acted_user_verified = False
        else:
            if self.last_acted_user_id and hasattr(self.last_acted_user, 'profile'):
                self.last_acted_user_username = self.last_acted_user.profile.username
                self.last_acted_user_url = self.last_acted_user.profile.get_absolute_url()
                self.last_acted_user_verified = self.last_acted_user.profile.verified

            if not only_user:
                # this is called only after question is created or edited
                self.tag_names = ', '.join(list(self.question_hashtags.values_list('name', flat=True)))
                fields_to_update.append('tag_names')

        self.save(update_fields=fields_to_update)

    def number_active_answers(self):
        answer_counter = 0
        for a in self.question_answers.filter(is_active=True, soft_deleted=False):
            if a.user_id and a.user.profile.is_active:
                answer_counter += 1
        return answer_counter

    def sync_number_answers(self):
        self.number_answers = self.number_active_answers()
        self.save(update_fields=['number_answers'])

    def update_number_views(self):
        self.views = self.question_views.count()
        self.save(update_fields=['views'])

    def increase_views_counter(self, request):
        source_ip = IP(request=request).user_ip()
        user = request.user if request.user.is_authenticated else None

        # we dont increase counter if user has no IP.
        if not source_ip:
            return

        if not self.question_views.filter(source_ip=source_ip).count():
            views_counter = self.question_views.create(
                source_ip=source_ip
            )
            if user:
                views_counter.user_id = user.id
                views_counter.save()
            self.update_number_views()
        else:
            latest_entry = self.question_views.filter(source_ip=source_ip).order_by('-id')[0]
            five_minutes_ago = (timezone.now() - timezone.timedelta(minutes=5))
            if latest_entry.idate <= five_minutes_ago:
                views_counter = self.question_views.create(
                    source_ip=source_ip
                )
                if user:
                    views_counter.user_id = user.id
                    views_counter.save()
                self.update_number_views()

    def is_article(self):
        return self.type == 'article'

    def is_incomplete_and_on_hold(self):
        return self.question_reports.filter(reason='incomplete').count() >= 5

    def re_rank(self, reason='', last_acted_user=None, repopulate=True):
        self.rank_date = timezone.now()
        self.rank_reason = reason
        if last_acted_user:
            self.last_acted_user = last_acted_user
        self.save()

        if repopulate:
            if 'gefragt' in reason or 'geändert' in reason:
                self.populate_speed_fields()
            else:
                self.populate_speed_fields(only_user=True)

    @classmethod
    def question_already_asked(cls, question_title):
        """
        checks the latest 100 questions if the new question is already asked with same body content
        """
        new_checksum = hashlib.md5(question_title.encode('utf-8')).hexdigest()
        for question in Question.objects.order_by('-id')[:100]:
            old_checksum = hashlib.md5(question.title.encode('utf-8')).hexdigest()
            if old_checksum == new_checksum:
                return True

        return False

    def inform_about_downvote(self, reason=''):
        if not settings.DEBUG:
            send_email_in_template(
                "Deine Antwort hat einen Downvote erhalten.",
                [self.user.email],
                **{
                    'text': 'Deine Frage hat einen Downvote erhalten.'
                            '<p>Begründung: <em>%s</em></p>'
                            'hier ist der Link zu der Frage: <br> <a href="https://%s%s">"%s"</a>'
                            '<p>'
                            % (
                                reason, settings.DOMAIN, self.get_absolute_url(), self.title
                            )
                }
            )

    def inform_browser_about_new_answer(self, user_id=None):
        if not settings.DEBUG and settings.ENABLE_WEBSOCKETS:
            new_answer_payload = {
                'type': 'new_answer',
                'user_id': user_id
            }
            try:
                ws = create_connection(settings.WEBSOCKET_QUESTION_PUSH_DOMAIN % self.id)
                ws.send(json.dumps(new_answer_payload))
                ws.close()
            except Exception:
                pass

    def inform_browser_about_new_comment(self, comment_type, belongs_to, comment_text, username, user_id):
        if not settings.DEBUG and settings.ENABLE_WEBSOCKETS:
            new_comment_payload = {
                'type': comment_type,
                'belongs_to': belongs_to,
                'comment_text': comment_text,
                'username': username,
                'user_id': user_id
            }

            try:
                ws = create_connection(settings.WEBSOCKET_QUESTION_PUSH_DOMAIN % self.id)
                ws.send(json.dumps(new_comment_payload))
                ws.close()
            except Exception:
                pass

    def latest_question_answers(self):
        return self.question_answers.filter(soft_deleted=False).order_by(
            '-accepted', '-vote_points', 'idate'
        )

    def all_question_comments(self):
        return self.question_comments.order_by('id')

    def make_inactive(self):
        self.is_active = False
        self.save()

        # inform the owner
        if self.user_id and self.user.email:
            send_email_in_template(
                "Leider scheint deine Frage Unstimmigkeiten zu enthalten",
                [self.user.email],
                **{
                    'text': '<p>Leider scheint deine Frage Unstimmigkeiten zu enthalten und wurde deshalb gemeldet:'
                            ' <a href="https://%s%s">"%s"</a>.</p>'
                            '<p>'
                            'Wir bitten dich daher deine Frage zu korrigieren. Solange dies nicht passiert ist, '
                            'bleibt deine Frage unsichtbar.'
                            '</p>'
                            % (
                                settings.DOMAIN, self.get_absolute_url(), self.title
                            )
                }
            )

    @property
    def votes(self):
        return self.question_votes.filter(type='up').count() - self.question_votes.filter(type='down').count()

    def update_votes(self, new_points=None):
        if new_points:
            print('removing points?')
            self.user.profile.increase_points(points=new_points, reason='got_vote')
        self.vote_points = self.votes
        self.save(update_fields=['vote_points'])

    @property
    def slug(self):
        slugged = slugify(self.title)
        if not slugged:
            slugged = slugify(self.text[:100])

        if not slugged:
            slugged = '--empty--'

        return slugged

    def get_absolute_url(self):
        slug = self.slug

        return reverse('question_detail_hashed', kwargs={
            'hash_id': self.hash_id, 'slug': slug
        })

    def get_absolute_admin_url(self):
        return 'https://%s%s' % (
            settings.DOMAIN, reverse('admin:question_question_change', args=(self.id,))
        )

    def answered(self):
        return self.number_answers > 0 and self.closed

    def inform_involved_users(self, message='', notification_type='', exclude_users=None):

        msg = Message.objects.create(
            title=self.title,
            message=message,
            link=self.get_absolute_url(),
            type=notification_type
        )
        self.refresh_from_db()

        if not hasattr(self, 'involved_peeps'):
            return

        users_to_inform = self.involved_peeps.users.all()

        if exclude_users:
            users_to_inform = users_to_inform.exclude(id__in=exclude_users)

        if settings.ENABLE_WEBSOCKETS:
            for user in users_to_inform:
                msg.to_users.add(user)
                try:
                    ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % user.id)
                    ws.send(notification_type)
                    ws.close()
                except Exception:
                    continue

    def inform_questioner(self, answer):
        """
        notify question owner via email and app push
        """

        if not self.user_id:
            return

        if not answer.user_id:
            return

        if self.user_id == answer.user_id:
            return

        if self.user.email:
            send_email_in_template(
                "Neue Antwort zu deiner Frage",
                [self.user.email],
                **{
                    'text': '<p>%s hat deine Frage beantwortet.</p>'
                            '<p><b>Wichtig:</b> Bitte vergiss nicht, die Antwort zu akzeptieren, '
                            'die dir am meisten geholfen hat. So akzeptierst du eine Antwort:</p>'
                            '<p><img src="http://media.mathefragen.de/static/images/accept3.gif" width="100%%"></p>' % answer.user.profile.username,
                    'link': 'https://%s%s#post_%s' % (
                        settings.DOMAIN, self.get_absolute_url(), answer.id
                    ),
                    'link_name': 'Jetzt Antwort sehen'
                }
            )

        fcm_token = self.user.profile.fcm_token

        if fcm_token:
            push_service = FCMNotification(api_key=settings.FIREBASE_SERVER_KEY)
            push_service.notify_single_device(
                registration_id=fcm_token,
                message_title='Du hast eine Antwort auf deine Frage erhalten!',
                message_body='Klick hier, um die Antwort zu sehen',
                data_message={
                    'to_user_id': self.user_id,
                    'question_id': self.id,
                }
            )

    def repair_images(self):
        question_text = self.text

        question_text = question_text.replace('../../media/', '/media/')
        question_text = question_text.replace('src="../', 'src="')

        # fix image rotation
        RepairImages(text=question_text).start()

        # fix image urls
        pattern = re.compile('<img src="(.*?)" />')
        question_text = pattern.sub(r'<img src="\1" class="fit_width" />', question_text)
        self.text = question_text
        self.save()

    def __str__(self):
        return '[%s] %s' % (self.id, self.title[:70])


class QuestionInvolvedUsers(models.Model):
    question = models.OneToOneField(Question, related_name='involved_peeps', on_delete=models.CASCADE)
    users = models.ManyToManyField(User)


def follow_question(self, question_id):
    question = Question.objects.get(id=question_id)
    question.followers.add(self)


def unfollow_question(self, question_id):
    question = Question.objects.get(id=question_id)
    question.followers.remove(self)


User.add_to_class('follow_question', follow_question)
User.add_to_class('unfollow_question', unfollow_question)


class Answer(Base):
    user = models.ForeignKey(
        User,
        related_name='user_answers',
        on_delete=models.CASCADE,
        null=True
    )
    question = models.ForeignKey(Question, related_name='question_answers', on_delete=models.CASCADE, null=True)
    text = models.TextField()
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    grasp_level = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    vote_points = models.IntegerField(default=0, blank=True)
    soft_deleted = models.BooleanField(default=False)
    soft_deleted_at = models.DateTimeField(null=True, blank=True)
    source_ip = models.GenericIPAddressField(default='192.168.0.1')
    edited_by = models.ForeignKey(
        User,
        related_name='edited_answers',
        null=True,
        on_delete=models.SET_NULL
    )
    edited_at = models.DateTimeField(null=True)

    def delete(self, using=None, keep_parents=False):
        if self.user_id and self.user.profile.total_answers >= 1:
            self.user.profile.total_answers -= 1
            self.user.profile.save()

        self.soft_deleted = True
        self.is_active = False
        self.soft_deleted_at = timezone.now()
        self.save()

    def can_be_edited(self):
        if self.user.profile.is_moderator():
            return True

        # question is not editable anymore after 24 hours.
        return self.idate > (timezone.now() - timezone.timedelta(hours=24))

    def can_be_deleted(self):
        """
        Answer can not be deleted if:
         1. it has been accepted:
         2. not reached 5 deletions of own posts per day.

        if the owner is mod, he can delete his posts anytime.
        """
        if self.user.profile.is_moderator():
            return True

        deletions_today = self.user.user_answers.filter(soft_deleted_at__date=timezone.now().date()).count()
        if deletions_today < 5 and not self.accepted:
            return True

        return False

    def make_inactive(self):
        self.is_active = False
        self.save()

        # check

        # inform the owner
        send_email_in_template(
            "Leider scheint deine Antwort Unstimmigkeiten zu enthalten",
            [self.user.email],
            **{
                'text': 'Leider scheint deine Antwort Unstimmigkeiten zu enthalten und '
                        'wurde deshalb gemeldet: <a href="https://%s%s">"%s"</a>'
                        '<p>'
                        'Wir bitten dich daher deine Antwort zu korrigieren. Solange dies nicht passiert ist, '
                        'wird deine Antwort ausgegraut bleiben und kann weder positive Votes erhalten, '
                        'noch kommentiert, oder akzeptiert werden.'
                        '</p>'
                        % (
                            settings.DOMAIN, self.question.get_absolute_url(), self.text[:50]
                        )
            }
        )

    def set_accepted(self, grasp_level=None):
        self.accepted = True
        self.accepted_at = timezone.now()
        if grasp_level:
            self.grasp_level = grasp_level
        self.save()

        self.question.closed = True
        self.question.answerer_id = self.user_id
        self.question.save()

    def inform_about_downvote(self, reason=''):
        send_email_in_template(
            "Deine Antwort hat einen Downvote erhalten.",
            [self.user.email],
            **{
                'text': 'Deine Antwort hat einen Downvote erhalten.'
                        '<p>Begründung: <em>%s</em></p>'
                        'hier ist der Link zu der Frage: <br> <a href="https://%s%s">"%s"</a>'
                        '<p>'
                        % (
                            reason, settings.DOMAIN, self.question.get_absolute_url(), self.question.title
                        )
            }
        )

    def inform_answerer(self):
        if settings.ENABLE_WEBSOCKETS:
            msg = Message.objects.create(
                title='Antwort akzeptiert',
                message='Deine Antwort wurde von %s akzeptiert.' % self.question.user.profile.username,
                link=self.question.get_absolute_url(),
                type='Akzeptiert'
            )
            msg.to_users.add(self.user)
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % self.user_id)
                ws.send('Akzeptiert')
                ws.close()
            except Exception:
                pass

    def all_answer_comments(self):
        return self.answer_comments.order_by('id')

    @property
    def votes(self):
        return self.answer_votes.filter(type='up').count() - self.answer_votes.filter(type='down').count()

    def update_votes(self, new_points=None):
        if new_points:
            self.user.profile.increase_points(points=new_points, reason='got_vote')
        self.vote_points = self.votes
        self.save(update_fields=['vote_points'])

    def __str__(self):
        return self.text[:100]

    def get_absolute_url(self):
        return '%s#post_%s' % (
            self.question.get_absolute_url(),
            self.id
        )

    def get_absolute_admin_url(self):
        return 'https://%s%s' % (
            settings.DOMAIN, reverse('admin:question_answer_change', args=(self.id,))
        )

    class Meta:
        ordering = ('-id',)


class AnswerRecommendation(Base):
    answer = models.ForeignKey(Answer, related_name='answer_recommendations', on_delete=models.CASCADE)
    youtube_id = models.CharField(max_length=20, default='')
    soft_deleted = models.BooleanField(default=False)

    def __str__(self):
        return 'Answer[%s] Recommendation [%s]' % (self.answer_id, self.id)


class AnswerComment(Base):
    answer = models.ForeignKey(Answer, related_name='answer_comments', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, related_name='user_answer_comments', on_delete=models.CASCADE, null=True)
    text = models.TextField()
    soft_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    vote_points = models.IntegerField(default=0, blank=True)
    source_ip = models.GenericIPAddressField(default='192.168.0.1')

    def get_absolute_url(self):
        slug = slugify(self.answer.question.title)
        if not slug:
            slug = slugify(self.answer.question.text[:100])

        return '%s#answer_comment_%s' % (
            reverse('question_detail', kwargs={
                'question_id': self.answer.question_id, 'slug': slug
            }),
            self.id
        )

    def get_absolute_link(self):
        return 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url())

    def __str__(self):
        return '%s .. [%s]' % (
            self.text[:100], self.id
        )


class QuestionComment(Base):
    question = models.ForeignKey(Question, related_name='question_comments', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, related_name='user_question_comments', on_delete=models.CASCADE, null=True)
    text = models.TextField()
    is_active = models.BooleanField(default=True)
    vote_points = models.IntegerField(default=0, blank=True)
    soft_deleted = models.BooleanField(default=False)
    source_ip = models.GenericIPAddressField(default='192.168.0.1')

    def get_absolute_url(self):
        slug = slugify(self.question.title)
        if not slug:
            slug = slugify(self.question.text[:100])

        return '%s#question_comment_%s' % (
            reverse('question_detail', kwargs={
                'question_id': self.question_id, 'slug': slug
            }),
            self.id
        )

    def get_absolute_link(self):
        return 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url())

    def __str__(self):
        return '%s .. [%s]' % (
            self.text[:100], self.id
        )
