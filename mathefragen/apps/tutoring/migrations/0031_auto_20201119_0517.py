# Generated by Django 2.1.1 on 2020-11-19 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0030_auto_20201116_1739'),
    ]

    operations = [
        migrations.AddField(
            model_name='helprequest',
            name='student_joined_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='helprequest',
            name='tutor_joined_at',
            field=models.DateTimeField(null=True),
        ),
    ]
