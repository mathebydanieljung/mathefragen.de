# Generated by Django 2.1.1 on 2020-08-24 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20200824_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='filled_data_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
