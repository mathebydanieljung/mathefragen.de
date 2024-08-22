from django.db import models
from django.shortcuts import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base


class News(Base):
    author = models.ForeignKey(
        User,
        related_name='user_news',
        on_delete=models.SET_NULL,
        null=True
    )
    title = models.CharField(max_length=200)
    text = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('detail_news', kwargs={
            'hash_id': self.hash_id, 'slug': slugify(self.title)
        })

    class Meta:
        verbose_name_plural = 'Artikeln'
        verbose_name = 'Artikel'


class ReleaseNote(News):
    version = models.CharField(max_length=50, help_text='e.g. 1.0.0, 1.1.0, 1.1.1', default='')
    public_date = models.DateTimeField(null=True, blank=True)
    public = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('details_release_note', kwargs={
            'hash_id': self.hash_id, 'slug': slugify(self.title)
        })

    class Meta:
        verbose_name_plural = 'Release Notes'
        verbose_name = 'Release Note'


class ReadReleaseNote(models.Model):
    idate = models.DateTimeField(auto_now_add=True, db_index=True)
    release_note = models.ForeignKey(
        ReleaseNote,
        related_name='read_release_notes',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='user_read_release_notes',
        on_delete=models.CASCADE
    )
