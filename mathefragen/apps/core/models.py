import codecs
import os
import random

from django.db import models


def create_default_hash(length=5):
    return codecs.encode(os.urandom(length), 'hex').decode()


def random_five_digits():
    return random.randint(111111, 999999)


class Base(models.Model):
    hash_id = models.CharField(
        default=create_default_hash,
        editable=False,
        max_length=30,
        db_index=True
    )
    idate = models.DateTimeField(auto_now_add=True, verbose_name='created at', db_index=True)
    udate = models.DateTimeField(auto_now=True, verbose_name='changed at')

    class Meta:
        abstract = True


class BaseAddress(models.Model):
    COUNTRIES = (
        ('de', 'Deutschland'),
        ('at', 'Österreich'),
        ('ch', 'Schweiz'),
    )
    address1 = models.CharField(
        max_length=1024,
    )

    address2 = models.CharField(
        max_length=1024,
        blank=True
    )

    zip_code = models.CharField(
        max_length=12,
    )

    city = models.CharField(
        max_length=1024,
    )

    state = models.CharField(
        default='',
        max_length=1024,
        blank=True
    )

    country = models.CharField(
        default='de',
        max_length=1024,
        blank=True,
        choices=COUNTRIES
    )

    class Meta:
        abstract = True

