# Generated by Django 2.2 on 2020-12-14 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0019_profile_most_helped_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='total_answer_comments',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='total_question_comments',
            field=models.IntegerField(default=0),
        ),
    ]
