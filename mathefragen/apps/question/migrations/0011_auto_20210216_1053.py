# Generated by Django 2.2 on 2021-02-16 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('question', '0010_question_answerer'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='accepted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='soft_deleted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='soft_deleted_at',
            field=models.DateTimeField(null=True),
        ),
    ]
