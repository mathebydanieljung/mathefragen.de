# Generated by Django 2.1.1 on 2020-11-24 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0032_tutorsetting_payment_change_cancelled_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='helprequest',
            old_name='completed_at',
            new_name='student_completed_at',
        ),
        migrations.AddField(
            model_name='helprequest',
            name='tutor_completed_at',
            field=models.DateTimeField(null=True),
        ),
    ]
