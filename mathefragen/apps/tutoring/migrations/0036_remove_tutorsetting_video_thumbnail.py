# Generated by Django 2.1.1 on 2020-11-26 16:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0035_tutorsetting_video_thumbnail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tutorsetting',
            name='video_thumbnail',
        ),
    ]
