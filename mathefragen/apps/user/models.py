import datetime
import json
import operator
import random
from io import BytesIO

import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import default_storage as storage
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from rest_framework_simplejwt.settings import api_settings

from mathefragen.apps.core.models import Base, BaseAddress
from mathefragen.apps.core.utils import (
    send_email_in_template,
    create_default_hash,
    generate_cool_number
)
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.news.models import ReleaseNote
from mathefragen.apps.playlist.models import Playlist
from mathefragen.apps.question.models import Question, Answer


class PostalCode(models.Model):
    code = models.IntegerField(db_index=True)
    city = models.CharField(max_length=100, default='', blank=True)
    district = models.CharField(max_length=100, default='', blank=True)
    county = models.CharField(max_length=100, default='', blank=True)
    state = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        return str(self.code)


class Institution(models.Model):
    TYPES = (
        ('schule', 'Schule'),
        ('uni', 'Uni')
    )
    type = models.CharField(max_length=20, choices=TYPES, blank=True, default='')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PointState(models.Model):
    REASONS = (
        ('got_vote', 'Received Vote'),  # 5
        ('helped', 'Helped (given Answer is accepted by question-giver)'),  # 15
        ('accepted', 'Accepted Answer')  # 2
    )
    idate = models.DateTimeField(auto_now_add=True)
    new_points = models.IntegerField(default=0)
    reason = models.CharField(max_length=20, choices=REASONS, default='')
    total_points = models.IntegerField(default=0)
    user = models.ForeignKey(User, related_name='user_points', on_delete=models.CASCADE)


class KnowledgeState(models.Model):
    idate = models.DateTimeField(auto_now_add=True)
    new_knowledge = models.IntegerField()
    total_knowledge = models.IntegerField(default=10)
    user = models.ForeignKey(
        User,
        related_name='user_knowledge_states',
        on_delete=models.CASCADE
    )


class HelperState(models.Model):
    """
    top: once every week
    stetig: once every month
    """
    TYPES = (
        ('top', 'Top Helfer'),
        ('stetig', 'Stetiger Helfer')
    )
    date = models.DateField(
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        related_name='user_help_stats',
        on_delete=models.CASCADE
    )
    type = models.CharField(
        choices=TYPES,
        max_length=10,
        default='',
        blank=True
    )


class Badge(Base):
    """
    Moderator can:
    - soft-delete questions/answers
    - edit questions/answers
    - edit / delete tags
    - can see deleted posts (question or answer)
    """

    TYPES = (
        ('mod', 'Moderator'),
    )
    name = models.CharField(max_length=100)
    power_report = models.BooleanField(
        default=False,
        help_text='1 report = 3 reports'
    )
    can_edit_questions = models.BooleanField(default=False)
    can_edit_answers = models.BooleanField(default=False)

    # todo: remove fields and bind the permissions to a type.

    def __str__(self):
        return self.name


class Profile(Base):
    STATUS = (
        ('schueler', 'Schüler'),
        ('student', 'Student'),
        ('auszubildender', 'Auszubildender'),
        ('lehrer_prof', 'Lehrer/Professor'),
        ('sonstiges', 'Sonstiger Berufsstatus')
    )
    BADGES = (
        ('top_helper', 'Top Helper'),
        ('top_helper', 'frequent helper'),
    )
    GENDER = (
        ('m', 'männlich'),
        ('f', 'weiblich'),
    )

    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete=models.CASCADE,
        verbose_name='auth user'
    )
    badges = models.ManyToManyField(
        Badge,
        blank=True
    )
    social_sign = models.CharField(max_length=100, default='', blank=True)
    bio_text = models.TextField(default='', blank=True)
    skills = models.TextField(default='', blank=True)
    fcm_token = models.TextField(default='', blank=True)
    confirm_hash = models.CharField(max_length=60, default='', blank=True)
    pw_onetime_hash = models.CharField(max_length=60, default='', blank=True)

    verified = models.BooleanField(
        default=False,
        help_text="Wenn zum ersten Mal aktiviert, erhält User eine E-Mail Benachrichtung."
    )
    helper_detected_at = models.DateTimeField(null=True)
    profile_image = models.ImageField(upload_to='user/', default='', blank=True)

    found_us_in = models.CharField(max_length=100, default='', blank=True)

    # stats
    points = models.IntegerField(default=0, db_index=True)
    knowledge_state = models.IntegerField(default=0)
    reached_ppl = models.IntegerField(default=0)
    total_answers = models.IntegerField(default=0, db_index=True)
    answers_this_month = models.IntegerField(default=0, db_index=True)
    answered_month = models.IntegerField(default=0, db_index=True)
    answers_this_week = models.IntegerField(default=0, db_index=True)
    answered_week = models.IntegerField(default=0, db_index=True)
    total_questions = models.IntegerField(default=0, db_index=True)
    total_question_comments = models.IntegerField(default=0)
    total_answer_comments = models.IntegerField(default=0)
    most_helped_tags = models.CharField(max_length=1024, default='', blank=True)

    # fields for stats, these fields will not be reset
    number_asks = models.IntegerField(default=0)

    wp_id = models.IntegerField(null=True, blank=True)
    origin = models.CharField(max_length=50, default='local-webapp', blank=True)

    # privacy settings
    hide_email = models.BooleanField(default=False)
    hide_full_name = models.BooleanField(default=False)
    hide_username = models.BooleanField(default=False)

    # user meta info
    postal_code = models.ForeignKey(
        PostalCode,
        related_name='users_in_this_area',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    institution = models.ForeignKey(
        Institution, related_name='students', on_delete=models.SET_NULL, null=True, blank=True
    )
    phone_number = models.CharField(max_length=100, default='', blank=True)
    degree_course = models.CharField(max_length=100, default='', blank=True)
    degree_grade = models.CharField(max_length=100, default='', blank=True)
    status = models.CharField(max_length=50, choices=STATUS, default='', blank=True)
    other_status = models.CharField(max_length=1024, default='', blank=True)
    gender = models.CharField(max_length=50, choices=GENDER, default='', blank=True)
    birth_year = models.IntegerField(blank=True, null=True)

    filled_data_at = models.DateTimeField(null=True, blank=True)
    skipped_data_at = models.DateTimeField(null=True, blank=True)
    can_tutor = models.BooleanField(default=False, verbose_name='Kann Nachhilfeunterricht geben')
    total_tutored = models.IntegerField(default=0)

    # number of reports given to the contents of this user
    reported = models.IntegerField(default=0)
    last_active = models.DateTimeField(null=True)
    soft_deleted = models.BooleanField(default=False)
    # sync between other portals
    synced = models.BooleanField(default=False)

    def remove_ip_trace(self):
        """
        it just resets to default router gateway
        """
        user = self.user
        # in comments
        user.user_answer_comments.update(source_ip='192.168.0.1')
        user.user_question_comments.update(source_ip='192.168.0.1')
        # in questions & answers
        user.user_questions.update(source_ip='192.168.0.1')
        user.user_answers.update(source_ip='192.168.0.1')
        # playlist
        user.user_playlists.update(source_ip='192.168.0.1')
        # views
        user.user_question_views.update(source_ip='192.168.0.1')
        user.user_playlist_views.update(source_ip='192.168.0.1')

    def has_reached_helper_level(self):
        return self.points >= 300 and self.user.user_answers.count() >= 30

    def is_energetic(self):
        """
        :return: True if user has been active on site in the last 4 days
        """
        if not self.last_active:
            return False

        return timezone.now() < (self.last_active + timezone.timedelta(days=7))

    def all_tutor_sessions(self):
        return (self.user.received_help_requests.all() | self.user.sent_help_requests.all()).order_by('-idate')

    def latest_tutoring_sessions(self):
        if self.all_tutor_sessions().count():
            return self.all_tutor_sessions()[:6]

    def get_time_price(self, duration='30'):
        if not hasattr(self.user, 'tutor_setting'):
            return 0.0
        tutoring_settings = self.user.tutor_setting
        time_price = {
            '30': tutoring_settings.half_hourly_rate,
            '60': tutoring_settings.hourly_rate,
            '90': tutoring_settings.ninety_min_rate
        }
        return time_price.get(duration)

    def total_tutoring_sessions(self):
        now = timezone.now()
        completed_sessions = self.user.received_help_requests.filter(
            paid_at__isnull=False,
            tutor_completed_at__lt=(now - timezone.timedelta(minutes=10)),
            student_completed_at__lt=(now - timezone.timedelta(minutes=10))
        ).count()
        # todo: set total_tutored and use it. less db query
        return completed_sessions

    def can_see_deleted_content(self):
        if self.points > 5000:
            return True
        if self.can_edit_questions():
            return True
        return False

    def update_question_speed_fields(self, reset=False):
        for q in self.user.user_questions.all():
            q.populate_speed_fields(reset=reset)
        for a in self.user.user_answers.all():
            a.question.populate_speed_fields(reset=reset)

    def close_user_questions(self):
        self.user.user_questions.update(soft_deleted=True)

    def has_confirmed_email(self):
        return 'confirmed' in self.confirm_hash

    def can_give_tutoring(self):
        # email must be verified
        if 'confirmed' not in self.confirm_hash:
            return False

        if not self.verified:
            return False

        # user has clicked on his tutor profile? if not, he/she is not a tutor.
        if not hasattr(self.user, 'tutor_setting'):
            return False

        tutor_setting = self.user.tutor_setting
        if not tutor_setting.is_active:
            return False

        if not tutor_setting.has_price():
            return False

        # user must be active in the last 4 days
        if not self.is_energetic():
            return False

        return self.can_tutor

    def get_profile_image(self):
        if self.profile_image:
            return self.profile_image.url
        identicon = 'https://www.gravatar.com/avatar/%s?s=100&d=identicon' % self.hash_id
        return identicon

    @property
    def should_complete_profile(self):
        # deactivated for now
        return False

        now = timezone.now()
        last_acted_date = self.filled_data_at
        if self.skipped_data_at and last_acted_date and last_acted_date < self.skipped_data_at:
            last_acted_date = self.skipped_data_at

        if not self.filled_data_at:
            last_acted_date = self.skipped_data_at

        if last_acted_date:
            # we wait 4 weeks since last activity of user on his data
            if now > (last_acted_date + timezone.timedelta(weeks=4)):
                # time is up, check if user has still incomplete profile
                incomplete_fields = self.incomplete_fields
                if incomplete_fields:
                    # dont ask in every page reload. just randomly
                    random_number = random.choice([*range(1, 41, 1)])
                    return random_number < 10 and (random_number % 2) == 0
        else:
            # user never acted on popups, either feature is new or user has all the data. just double check
            incomplete_fields = self.incomplete_fields
            if incomplete_fields:
                # dont ask in every page reload. just randomly
                random_number = random.choice([*range(1, 41, 1)])
                return random_number < 10 and (random_number % 2) == 0

        return False

    @property
    def incomplete_fields(self):
        missing_fields = []
        if not self.postal_code_id:
            missing_fields.append('postal_code')
        if not self.institution_id:
            missing_fields.append('institution')
        if not self.phone_number:
            missing_fields.append('phone_number')
        if not self.degree_course:
            missing_fields.append('degree_course')
        if not self.degree_grade:
            missing_fields.append('degree_grade')
        if not self.status:
            missing_fields.append('status')
        if not self.gender:
            missing_fields.append('gender')
        if not self.birth_year:
            missing_fields.append('birth_year')
        if not self.user.get_full_name():
            missing_fields.append('name')

        return missing_fields

    def is_moderator(self):
        # todo: adjust once badge is refactored
        return self.can_edit_questions()

    def can_edit_questions(self):
        return bool(self.badges.filter(can_edit_questions=True).count())

    def has_unread_updates(self):
        count_release_notes = ReleaseNote.objects.filter(public=True).count()
        count_read_release_notes = self.user.user_read_release_notes.count()
        return count_release_notes > count_read_release_notes

    def has_unseen_playlists(self):
        count_playlists = Playlist.objects.filter(is_active=True).count()
        count_seen_playlists = self.user.user_seen_playlists.count()
        return count_playlists > count_seen_playlists

    def has_seen_playlist(self, playlist_id):
        seen_playlist_ids = list(self.user.user_seen_playlists.values_list('playlist_id', flat=True))
        return playlist_id in seen_playlist_ids

    def all_playlists(self):
        return self.user.user_playlists.all()

    def finished_playlists(self):
        return self.user.user_playlists.annotate(
            units=models.Count('playlist_units')
        ).filter(units__gt=0, is_active=True).order_by('-vote_points')

    def following_content(self):
        question_ids = self.following_question_ids()
        return Question.objects.filter(type='question', id__in=question_ids).order_by('-rank_date')

    def following_question_ids(self):
        following_user_ids = list(self.user.following_users.values_list('following_id', flat=True))
        following_question_ids = list(self.user.following_questions.values_list('question_id', flat=True))
        following_hashtag_ids = list(self.user.following_hashtags.values_list('hashtag_id', flat=True))

        final_question_ids = list(Question.objects.filter(user_id__in=following_user_ids).values_list('id', flat=True))
        final_question_ids += list(Question.objects.filter(id__in=following_question_ids).values_list('id', flat=True))
        for tag_id in following_hashtag_ids:
            tag = HashTag.objects.get(id=tag_id)
            final_question_ids += list(tag.questions.values_list('id', flat=True))

        # remove duplicates
        return list(set(final_question_ids))

    def send_verification_email(self):
        send_email_in_template(
            "Dein Profil in %s ist jetzt verifiziert! 🥳🎉" % settings.DOMAIN,
            [self.user.email],
            **{
                'text': 'Hey %s, <p> Dein Profil auf <a href="https://%s%s">%s</a> ist jetzt verifiziert! 🥳🎉 </p>'
                        '<p>Dein Profil ist beachtenswert und aktiv.</p>'
                        '<p>Danke dass du im Portal fleißig mitmachst und den anderen mit deinen Antworten hilfst.</p>'
                        '<p>Wir freuen uns auf eine spannende Reise mit dir. </p>' % (
                            self.user.first_name or self.user.username, settings.DOMAIN,
                            reverse('public_profile_hashed', args=(self.hash_id,)), settings.DOMAIN
                        )
            }
        )

    def update_content_activeness(self):
        if not self.is_active:
            # deactivate all his/her questions, answers and comments
            self.user.user_questions.update(is_active=False)
            self.user.user_answers.update(is_active=False)
            self.user.user_answer_comments.update(is_active=False)
            self.user.user_question_comments.update(is_active=False)
        else:
            # activate all his/her questions, answers and comments
            self.user.user_questions.update(is_active=True)
            self.user.user_answers.update(is_active=True)
            self.user.user_answer_comments.update(is_active=True)
            self.user.user_question_comments.update(is_active=True)

    def increase_reports(self):
        self.reported += 1
        self.save(update_fields=['reported'])
        if not self.is_active and self.reported == 3:
            # deactivate all his/her questions, answers and comments
            self.user.user_questions.update(is_active=False)
            self.user.user_answers.update(is_active=False)
            self.user.user_answer_comments.update(is_active=False)
            self.user.user_question_comments.update(is_active=False)

            # remove user from top helpers
            self.answers_this_week = 0
            self.answers_this_month = 0
            self.save(update_fields=['answers_this_week', 'answers_this_month'])

            # email christian
            admin_url = '%suser/profile/?id=%s' % (settings.ADMIN_URL, self.id)
            send_email_in_template(
                "Behaviour von diesem User wurde mehrmals reported und User ist nun inaktiv",
                settings.ADMINS_TO_REPORT,
                **{
                    'text': 'Behaviour von diesem User wurde mehrmals reported und User ist nun inaktiv. '
                            'Link zum Admin: <a href="https://%s%s">Den User in Admin ansehen</a>'
                            % (
                                settings.DOMAIN, admin_url
                            )
                }
            )

    def sync_into_other_portals(self, origin=''):
        sync_payload = {
            'username': self.user.username,
            'password': self.user.password,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'status': self.status,
            'other_status': self.other_status,
            'bio_text': self.bio_text,
            'origin': origin,
            'source_s3_bucket': settings.AWS_STORAGE_BUCKET_NAME
        }
        if self.profile_image:
            try:
                sync_payload.update({
                    'profile_image_url': self.profile_image.url
                })
            except SuspiciousOperation:
                pass

        # remove current portal from the list, so that it does not sync in itself
        portals_to_sync = [p for p in settings.PORTALS_TO_SYNC if settings.DOMAIN not in p]
        for portal in portals_to_sync:
            requests.post(
                '%s/user/sync/' % portal,
                data=json.dumps(sync_payload),
                headers={'content-type': 'application/json'}
            )

        self.synced = True
        self.save(update_fields=['synced'])

    @property
    def is_active(self):
        return self.reported < 3

    def can_down_vote(self):
        """
        user can down-vote only if:
        - old enough
        - and has enough
        """
        old_enough = (self.user.date_joined + timezone.timedelta(days=30)) < timezone.now()
        can_down_vote_many_times = self.points > 100
        today_down_votes = self.user.user_votes.filter(type='down', idate__date=timezone.now().date()).count()
        if not old_enough:
            return False

        if can_down_vote_many_times:
            return True

        return today_down_votes <= 2

    def has_answered_twice(self, question_id):
        return self.user.user_answers.filter(question_id=question_id).count() > 1

    def update_number_answers(self, question_id=None, counter=1):

        # if user has already answered this question, skip the counter
        if question_id and self.has_answered_twice(question_id=question_id):
            return

        # numbers should not go below 0
        if counter < 0:
            if not self.total_answers:
                return

            if not self.answers_this_week:
                return

            if not self.answers_this_month:
                return

        self.total_answers += counter

        # check if this month is new, if not, +1, else =1
        if self.answered_month and self.answered_month != timezone.now().month:
            # reset month
            self.answered_month = timezone.now().month
            self.answers_this_month = counter
        else:
            # increase
            self.answered_month = timezone.now().month
            self.answers_this_month += counter

        # check if this week is new, if not, +1, else =1
        if self.answered_week and self.answered_week != timezone.now().isocalendar()[1]:
            # reset week
            self.answered_week = timezone.now().isocalendar()[1]
            self.answers_this_week = counter
        else:
            # increase
            self.answered_week = timezone.now().isocalendar()[1]
            self.answers_this_week += counter

        self.save(update_fields=[
            'answers_this_month',
            'answered_month',
            'answers_this_week',
            'answered_week',
            'total_answers'
        ])

    @classmethod
    def get_helper_ids(cls, from_date=None, to_date=None, slice_number=5):
        if not from_date:
            from_date = datetime.datetime(1970, 1, 1, 0, 0)

        if not to_date:
            to_date = timezone.now()

        helpers = {}
        for ans in Answer.objects.filter(idate__gte=from_date, idate__lt=to_date, user_id__isnull=False):
            if ans.user_id not in helpers:
                helpers[ans.user_id] = 1
            else:
                helpers[ans.user_id] += 1

        return sorted(helpers, key=helpers.get, reverse=True)[:slice_number]

    def number_helps_since(self, date=None):
        if not date:
            date = timezone.now() - timezone.timedelta(days=timezone.now().weekday())

        date = date.replace(hour=00, minute=00)

        number_helps = self.user.user_answers.filter(
            idate__gte=date, idate__lt=timezone.now()
        ).count()

        return number_helps

    @classmethod
    def top_helpers(cls, month=False, total=False, number=5):
        """
        top helpers per default for one week.
        """
        active_users = Profile.objects.filter(reported__lt=3, user__is_staff=False)
        final_helpers = active_users.filter(answers_this_week__gt=0).order_by('-answers_this_week')[:number]

        if month:
            final_helpers = active_users.filter(answers_this_month__gt=0).order_by('-answers_this_month')[:number]

        if total:
            final_helpers = active_users.filter(total_answers__gt=0).order_by('-total_answers')[:number]

        return final_helpers

    def is_top_helper(self, helpers=None):
        if not helpers:
            helpers = self.top_helpers()
        return self.user_id in [helper.id for helper in helpers]

    @property
    def get_badges(self):
        badges_to_show = list()
        if self.is_top_helper():
            badges_to_show.append('power Helfer')
            # check if helper state exists
            # todo: offload to somewhere else later, to avoid too many invocations.
            self.check_helper_state()

        if self.is_frequent_top_helper():
            badges_to_show.append('stetiger Helfer')

        for b in self.badges.all():
            badges_to_show.append(b.name)
        return badges_to_show

    def check_helper_state(self):
        """
        this function creates helper stats for the current week, if not exists yet.
        """

        this_week_of_calendar = timezone.now().isocalendar()[1]
        last_helper_state = self.user.user_help_stats.order_by('-id').first()

        if not last_helper_state:
            self.user.user_help_stats.create(
                date=timezone.now().date(),
                type='top'
            )
        else:
            if last_helper_state.date.isocalendar()[1] != this_week_of_calendar:
                self.user.user_help_stats.create(
                    date=timezone.now().date(),
                    type='top'
                )

    def is_frequent_top_helper(self):
        """
        if user helps for 3 weeks without break
        """
        top_helpers_this_week = self.top_helpers()
        top_helpers_this_month = self.top_helpers(month=True)

        return all([
            self.is_top_helper(helpers=top_helpers_this_week),
            self.is_top_helper(helpers=top_helpers_this_month)
        ])

    def asked_questions(self):
        return self.user.user_questions.filter(type='question')

    def written_articles(self):
        return self.user.user_questions.filter(type='article')

    def total_earnings_as_tutor(self):
        """
        we show earnings once session is over and 10 minutes past.
        This number shows the netto earnings, our commission already subtracted.
        """
        now = timezone.now()
        total_earnings = self.user.received_help_requests.filter(
            paid_at__isnull=False,
            tutor_completed_at__lt=(now - timezone.timedelta(minutes=10)),
            student_completed_at__lt=(now - timezone.timedelta(minutes=10))
        ).aggregate(
            total=models.Sum('users_share')
        ).get('total', 0)
        return total_earnings if total_earnings else 0

    def payable_amount(self):
        current_earnings = self.current_earnings_as_tutor()
        pending_requests = self.user.tutor_payouts.filter(status='pending').aggregate(
            total=models.Sum('amount')
        ).get('total', 0)
        pending_requests = pending_requests if pending_requests else 0
        return current_earnings - pending_requests

    def current_earnings_as_tutor(self):
        total_payouts = self.user.tutor_payouts.filter(status='paid').aggregate(
            total=models.Sum('amount')
        ).get('total', 0)
        total_payouts = total_payouts if total_payouts else 0
        return self.total_earnings_as_tutor() - total_payouts

    @property
    def get_full_name(self):
        if self.hide_full_name:
            return self.username

        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.username

    @property
    def username(self):
        if self.hide_username:
            return 'anonym%s' % self.hash_id[:5]
        return self.user.username

    def helped_hashtag_ids(self):
        question_ids = list(self.user.user_answers.values_list('question_id', flat=True))
        used_hashtags_in_questions = HashTag.objects.filter(
            questions__in=Question.objects.filter(id__in=question_ids)
        )
        return used_hashtags_in_questions.values('id', 'name').order_by('?')[:20]

    def update_most_helped_tags(self):
        most_helped_tags = self.retrieve_most_helped_tags()
        self.most_helped_tags = most_helped_tags
        self.save(update_fields=['most_helped_tags'])

    def linked_most_helped_tags(self):
        split_most_helped_tags = self.most_helped_tags.split(',')
        final_tags = ''
        for idx, tag in enumerate(split_most_helped_tags):
            is_final_step = (idx + 1) == len(split_most_helped_tags)
            if '#' in tag:
                url_param = tag.replace('#', '')
                url_name = tag
            else:
                url_param = tag
                url_name = '#' + tag

            if not is_final_step:
                final_tags += '<a href="/tag/questions/?tag=%s" class="link_color">%s</a>, ' % (url_param, url_name)
            else:
                final_tags += '<a href="/tag/questions/?tag=%s" class="link_color">%s</a>' % (url_param, url_name)

        return final_tags

    def retrieve_most_helped_tags(self, number=6):
        question_ids = list(self.user.user_answers.values_list('question_id', flat=True))
        used_hashtags_in_questions = HashTag.objects.filter(questions__in=Question.objects.filter(id__in=question_ids))
        aggregated_tags = dict()
        for htag in used_hashtags_in_questions.all():
            hashtag = htag.name.lower()
            if hashtag in aggregated_tags:
                aggregated_tags[hashtag] += 1
            else:
                aggregated_tags[hashtag] = 1

        top_6_tags = sorted(aggregated_tags, key=aggregated_tags.get, reverse=True)[:number]
        final_tags = ','.join(top_6_tags)
        return final_tags

    def is_helper(self):
        return self.total_answers > 3

    def number_good_questions(self):
        return self.user.user_questions.filter(vote_points__gte=1, type='question', soft_deleted=False).count()

    def user_latest_questions(self):
        return self.user.user_questions.filter(type='question', soft_deleted=False).order_by('-id')

    def increase_reach(self, new_reached):
        self.reached_ppl = self.reached_ppl + new_reached
        self.save(update_fields=['reached_ppl'])

    def reputation_progress(self):
        """
        takes the interval from the beginning of month until now.
        takes the exact interval of last month
        and returns the increase/decrease amount with sign in front.
        """
        now = timezone.now()
        this_month_beginning = now - timezone.timedelta(days=(now.day - 1))

        this_month_points = self.user.user_points.filter(
            idate__gte=this_month_beginning, idate__lte=now
        ).aggregate(points=models.Sum('new_points')).get('points')

        if this_month_points and this_month_points >= 0:
            return this_month_points

        return 0

    def increase_points(self, points, reason=''):
        new_points = points

        total_points = self.points + new_points

        self.points = total_points
        self.save(update_fields=['points'])

        self.user.user_points.create(
            new_points=new_points, total_points=total_points, reason=reason
        )

    def increase_knowledge(self, more_knowledge):
        total_knowledge = self.knowledge_state + more_knowledge

        self.knowledge_state = total_knowledge
        self.save(update_fields=['knowledge_state'])

        self.user.user_knowledge_states.create(
            new_knowledge=more_knowledge, total_knowledge=total_knowledge
        )

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('public_profile_hashed', kwargs={
            'hash_id': self.hash_id
        })

    def has_confirmed_hashtags(self):
        return self.user.received_user_reviews.filter(hashtags__isnull=False).count()

    def confirmed_hashtags(self):
        # todo: save the tags dict in review object, instead of crawling from tags every time
        response_dict = {}
        for review in self.user.received_user_reviews.order_by('id'):
            for hashtag in review.hashtags.all():
                if hashtag.name in response_dict:
                    response_dict[hashtag.name] += 1
                else:
                    response_dict[hashtag.name] = 1

        return sorted(response_dict.items(), key=operator.itemgetter(1), reverse=True)

    def get_open_questions_url(self):
        return 'https://%s%s?filter=no_accept&user=%s' % (
            settings.DOMAIN, reverse('index'), self.user_id
        )

    @property
    def badge(self):
        return ''

    def send_email_confirmation(self, question_hash=''):
        confirm_hash = create_default_hash(length=12)
        self.confirm_hash = confirm_hash
        self.save()

        confirm_link = 'https://%s%s%s' % (
            settings.DOMAIN, reverse('register_confirm', kwargs={
                'confirm_hash': confirm_hash
            }),
            '?qh=%s' % question_hash if question_hash else ''
        )

        domain_name = settings.DOMAIN.replace('www.', '')
        send_email_in_template(
            'Willkommen bei mathefragen.de!',
            [self.user.email],
            **{
                'text': 'Hiii :)'
                        '<p>Danke, dass du dich bei %s angemeldet hast.</p>'
                        'Bitte klicke auf den Button, um deine E-Mail-Adresse zu bestätigen:' % domain_name,
                'link': confirm_link,
                'link_name': 'E-Mail-Adresse bestätigen'
            }
        )

    def generate_certificate(self):
        cert_template_path = 'https://media.mathefragen.de/static/images/certificate_template.jpg'

        template_image = Image.open(BytesIO(requests.get(cert_template_path).content))
        template_image.load()

        background = Image.new("RGB", template_image.size, (255, 255, 255))
        background.paste(template_image)

        draw = ImageDraw.Draw(background)

        # write user's full name
        nunito_regular_font_url = 'https://media.mathefragen.de/static/fonts/NunitoSans_Regular.ttf'
        nunito_bold_font_url = 'https://media.mathefragen.de/static/fonts/NunitoSans_Bold.ttf'

        name_font = ImageFont.truetype(BytesIO(requests.get(nunito_bold_font_url).content), 120)
        regular_name_font = ImageFont.truetype(BytesIO(requests.get(nunito_regular_font_url).content), 120)
        draw.text(
            (250, 500),
            '%s' % self.user.get_full_name(),
            (255, 255, 255),
            font=name_font
        )

        draw.text(
            (250, 700),
            'hat bisher %s mal geholfen,' % generate_cool_number(self.total_answers),
            (255, 255, 255),
            font=regular_name_font
        )
        draw.text(
            (250, 900),
            'war bisher %s mal Power-Helfer,' % generate_cool_number(self.user.user_help_stats.count()),
            (255, 255, 255),
            font=regular_name_font
        )
        draw.text(
            (250, 1100),
            'hat eine Reichweite von %s' % generate_cool_number(self.reached_ppl),
            (255, 255, 255),
            font=regular_name_font
        )

        # write the date
        date_font = ImageFont.truetype(BytesIO(requests.get(nunito_bold_font_url).content), 70)
        draw.text((2700, 2150), timezone.now().strftime('%d.%m.%Y'), (255, 255, 255), font=date_font)

        image_buffer = BytesIO()
        background.save(image_buffer, format='PDF')

        final_cert_path = 'certs/user_%s/certificate_%s_%s.pdf' % (
            self.user_id,
            self.user_id,
            create_default_hash(6)
        )

        image_file = storage.open(final_cert_path, 'wb')
        image_file.write(image_buffer.getvalue())
        image_file.flush()
        image_file.close()

        return final_cert_path

    def generate_jwt_token(self):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)

        return token


class Address(Base, BaseAddress):
    TYPES = (
        ('invoice', 'Rechnungsadresse'),
        ('postal', 'lieferadresse')
    )
    user = models.ForeignKey(
        User,
        related_name='user_addresses',
        on_delete=models.CASCADE
    )
    type = models.CharField(
        choices=TYPES,
        default='invoice',
        max_length=20
    )


class Social(Base):
    TYPES = (
        ('ytb', 'Youtube'),
        ('site', 'Webseite'),
        ('tw', 'Twitter'),
        ('xg', 'Xing'),
        ('insta', 'Instagram'),
        ('tt', 'TikTok'),
        ('in', 'LinkedIn')
    )
    user = models.ForeignKey(
        User,
        related_name='user_socials',
        on_delete=models.CASCADE
    )
    type = models.CharField(
        max_length=10,
        choices=TYPES,
        default='ytb'
    )
    link = models.TextField()
    description = models.TextField(
        max_length=140,
        help_text='max. 140 Zeichen'
    )
    soft_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.get_type_display()
