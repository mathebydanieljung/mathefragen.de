# Generated by Django 2.1.1 on 2020-11-30 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0033_auto_20201124_1220'),
    ]

    operations = [
        migrations.AddField(
            model_name='helprequest',
            name='users_share',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
