# Generated by Django 2.1.1 on 2020-11-19 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0031_auto_20201119_0517'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutorsetting',
            name='payment_change_cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
