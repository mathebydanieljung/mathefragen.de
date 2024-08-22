from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone

from mathefragen.apps.core.models import Base
from mathefragen.apps.core.utils import send_email_in_template
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.guardian.tools.ip import IP


class Playlist(Base):
    user = models.ForeignKey(
        User,
        related_name='user_playlists',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.ManyToManyField(
        HashTag
    )
    vote_points = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    source_ip = models.GenericIPAddressField(default='192.168.0.1')
    is_active = models.BooleanField(default=False)

    def update_number_views(self):
        self.views = self.playlist_views.count()
        self.save(update_fields=['views'])

    def increase_views_counter(self, request):
        source_ip = IP(request=request).user_ip()
        user = request.user if request.user.is_authenticated else None

        # we dont increase counter if user has no IP.
        if not source_ip:
            return

        if not self.playlist_views.filter(source_ip=source_ip).count():
            views_counter = self.playlist_views.create(
                source_ip=source_ip
            )
            if user:
                views_counter.user_id = user.id
                views_counter.save()
            self.update_number_views()
        else:
            latest_entry = self.playlist_views.filter(source_ip=source_ip).order_by('-id')[0]
            five_minutes_ago = (timezone.now() - timezone.timedelta(minutes=5))
            if latest_entry.idate <= five_minutes_ago:
                views_counter = self.playlist_views.create(
                    source_ip=source_ip
                )
                if user:
                    views_counter.user_id = user.id
                    views_counter.save()
                self.update_number_views()

    @property
    def votes(self):
        return self.playlist_votes.filter(type='up').count() - self.playlist_votes.filter(type='down').count()

    def update_votes(self, new_points=None):
        if new_points:
            self.user.profile.increase_points(points=new_points, reason='got_vote')
        self.vote_points = self.votes
        self.save(update_fields=['vote_points'])

    def make_inactive(self):
        self.is_active = False
        self.save()

        # inform the owner
        send_email_in_template(
            "Leider scheint deine Playlist Unstimmigkeiten zu enthalten",
            [self.user.email],
            **{
                'text': '<p>Leider scheint deine Playlist Unstimmigkeiten zu enthalten und wurde deshalb gemeldet:'
                        ' <a href="https://%s%s">"%s"</a>.</p>'
                        '<p>'
                        'Wir bitten dich daher deine Playlist zu korrigieren. Solange dies nicht passiert ist, '
                        'bleibt die Playlist unsichtbar.'
                        '</p>'
                        % (
                            settings.DOMAIN, self.get_absolute_url(), self.name
                        )
            }
        )

    def playlist_units_by_order(self):
        return self.playlist_units.order_by('int_order')

    @property
    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('playlist_detail', args=(self.slug, self.hash_id))

    def get_absolute_admin_url(self):
        return 'https://%s%s' % (
            settings.DOMAIN, reverse('admin:playlist_playlist_change', args=(self.id,))
        )

    def __str__(self):
        return self.name


class Unit(Base):
    playlist = models.ForeignKey(
        Playlist,
        related_name='playlist_units',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    media = models.FileField(
        default='',
        blank=True
    )
    int_order = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class VideoRecommendation(Base):
    unit = models.ForeignKey(Unit, related_name='unit_vid_recommendations', on_delete=models.CASCADE)
    youtube_id = models.CharField(max_length=20, default='')
    soft_deleted = models.BooleanField(default=False)

    def __str__(self):
        return 'Answer[%s] Recommendation [%s]' % (self.unit_id, self.id)


class LearntPlaylist(Base):
    user = models.ForeignKey(
        User,
        related_name='learnt_playlists',
        on_delete=models.CASCADE
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='learnt_traces',
        on_delete=models.CASCADE
    )


class LearntUnit(Base):
    user = models.ForeignKey(
        User,
        related_name='learnt_playlist_items',
        on_delete=models.CASCADE
    )
    unit = models.ForeignKey(
        Unit,
        related_name='learnt_traces',
        on_delete=models.CASCADE
    )


class SeenPlaylist(models.Model):
    idate = models.DateTimeField(auto_now_add=True, db_index=True)
    playlist = models.ForeignKey(
        Playlist,
        related_name='seen_playlists',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='user_seen_playlists',
        on_delete=models.CASCADE
    )



