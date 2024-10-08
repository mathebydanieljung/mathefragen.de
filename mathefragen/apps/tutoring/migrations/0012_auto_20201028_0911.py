# Generated by Django 2.1.1 on 2020-10-28 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0011_auto_20201028_0248'),
    ]

    operations = [
        migrations.RenameField(
            model_name='helprequest',
            old_name='needed_time',
            new_name='duration',
        ),
        migrations.AddField(
            model_name='helprequest',
            name='amount_to_pay',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
