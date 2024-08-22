# Generated by Django 2.1.1 on 2020-12-04 08:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutoring', '0037_merge_20201204_0833'),
    ]

    operations = [
        migrations.AddField(
            model_name='helprequest',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_help_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
