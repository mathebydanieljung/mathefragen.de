from django.db import models
from django.shortcuts import reverse
from django.utils.text import slugify

from mathefragen.apps.core.models import Base, create_default_hash
from mathefragen.apps.hashtag.models import HashTag


class Tag(models.Model):
    hash_id = models.CharField(
        default=create_default_hash,
        editable=False,
        max_length=30
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)

    def get_absolute_url(self):
        return '#get_absolute_url'

    def __str__(self):
        return self.name


class PlaylistCategory(models.Model):
    hash_id = models.CharField(
        default=create_default_hash,
        editable=False,
        max_length=30
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    def number_videos(self):
        count = 0
        for pl in self.playlists.all():
            count += pl.videos.count()
        return count

    def ordered_playlists(self):
        return self.playlists.order_by('order')

    @property
    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('category_detail', args=(self.slug, self.hash_id))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Playlist Kategorien'
        verbose_name = 'Playlist Kategorie'
        ordering = ('order',)


class Playlist(models.Model):
    hash_id = models.CharField(
        default=create_default_hash,
        editable=False,
        max_length=30
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200)
    description = models.TextField(default='', blank=True)
    thumbnail = models.ImageField(
        upload_to='playlist_thumbnail/%H/%M',
        default='',
        help_text='1280x720px',
        blank=True
    )
    category = models.ForeignKey(
        PlaylistCategory,
        related_name='playlists',
        on_delete=models.SET_NULL,
        null=True
    )
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    @property
    def slug(self):
        return slugify(self.title)

    def get_absolute_url(self):
        return reverse('playlist_detail', args=(self.slug, self.hash_id))

    def get_absolute_url_iframe(self):
        return reverse('playlist_detail_iframe', args=(self.slug, self.hash_id))

    def ordered_videos(self):
        return self.videos.order_by('order')

    class Meta:
        ordering = ['order']


class Video(models.Model):
    hash_id = models.CharField(
        default=create_default_hash,
        editable=False,
        max_length=30
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    OWNERS = (
        ('daniel', 'Daniel Jung'),
        ('max', 'Max Metelmann'),
        ('kai', 'Lehrer Schmidt'),
        ('rieke', 'Rieke Strehl'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.CharField(
        max_length=20,
        choices=OWNERS,
        blank=True,
        default='daniel'
    )
    thumbnail = models.ImageField(
        upload_to='video-thumbnail/%H/%M',
        default='',
        help_text='1280x720px',
        blank=True
    )
    youtube_hash = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )
    file = models.FileField(
        upload_to='videos/%H/%M',
        verbose_name='Video MP4 Datei'
    )
    original_size = models.FileField(
        upload_to='videos-orig/%H/%M',
        default='',
        blank=True,
        verbose_name='Video MP4 Datei (ORIGINAL SIZE)'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='videos_in_tag'
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='videos',
        blank=True,
        on_delete=models.SET_NULL,
        null=True
    )
    playlists = models.ManyToManyField(
        Playlist,
        related_name='playlist_videos',
        blank=True
    )
    order = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse('video_watch_view', kwargs={
            'hash_id': self.hash_id
        })

    def get_absolute_url_iframe(self):
        return reverse('video_detail_iframe', kwargs={
            'slug': self.slug,
            'video_hash': self.hash_id
        })

    @property
    def slug(self):
        return slugify(self.title)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
