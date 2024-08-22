# Generated by Django 2.1.1 on 2020-04-05 20:23

from django.db import migrations, models
import mathefragen.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('follow', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hashtagfollow',
            name='hash_id',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30),
        ),
        migrations.AlterField(
            model_name='questionfollow',
            name='hash_id',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30),
        ),
        migrations.AlterField(
            model_name='userfollow',
            name='hash_id',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30),
        ),
    ]
