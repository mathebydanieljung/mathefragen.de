# Generated by Django 2.1.1 on 2020-11-30 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0017_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='other_status',
            field=models.CharField(blank=True, default='', max_length=1024),
        ),
    ]
