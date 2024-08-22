# Generated by Django 2.2 on 2021-03-10 13:50

from django.db import migrations, models
import mathefragen.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('question', '0014_question_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='off_hash',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, max_length=30),
        ),
    ]
