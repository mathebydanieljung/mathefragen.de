# Generated by Django 2.1.1 on 2020-04-12 05:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mathefragen.apps.core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('playlist', '0001_squashed_0018_auto_20200708_2033'),
        ('question', '0001_squashed_0063_auto_20200728_0629'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportedAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('reason', models.CharField(choices=[('spam', 'Besteht nur, um ein Produkt oder eine Dienstleistung zu bewerben'), ('rude_abusive', 'Eine vernünftige Person würde diesen Inhalt für einen respektvollen Diskurs ungeeignet finden.'), ('general', 'Diese Antwort ist völlig unklar, unvollständig, übermäßig breit und es ist unwahrscheinlich, dass sie über die Bearbeitung behoben werden.'), ('duplicate', 'Diese Antwort ist überflüßig und möglicherweise ein Copy-Paste.'), ('bad_quality', 'Diese Antwort hat schwerwiegende Formatierungs- oder Inhaltsprobleme. Es ist unwahrscheinlich, dass diese Antwort durch die Bearbeitung zu retten ist und möglicherweise entfernt werden muss.'), ('need_moderator_attention', 'Ein Problem, das oben nicht aufgeführt ist, erfordert die Reaktion eines Moderators.'), ('incomplete', 'Diese Antwort hat lückenhafte Angaben.')], default='general', max_length=50)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_reports', to='question.Answer')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_answer_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportedPlaylist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('reason', models.CharField(default='general', max_length=50)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlist_reports', to='playlist.Playlist')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_playlist_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportedQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('reason', models.CharField(choices=[('spam', 'Besteht nur, um ein Produkt oder eine Dienstleistung zu bewerben'), ('rude_abusive', 'Eine vernünftige Person würde diesen Inhalt für einen respektvollen Diskurs ungeeignet finden.'), ('general', 'Diese Frage ist völlig unklar, unvollständig, übermäßig breit und es ist unwahrscheinlich, dass sie über die Bearbeitung behoben werden.'), ('duplicate', 'Diese Frage wurde bereits gestellt und hat bereits eine Antwort.'), ('bad_quality', 'Diese Frage hat schwerwiegende Formatierungs- oder Inhaltsprobleme. Es ist unwahrscheinlich, dass diese Frage durch die Bearbeitung zu retten ist und möglicherweise entfernt werden muss.'), ('need_moderator_attention', 'Ein Problem, das oben nicht aufgeführt ist, erfordert die Reaktion eines Moderators.'), ('incomplete', 'Diese Frage hat lückenhafte Angaben.')], default='general', max_length=50)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_reports', to='question.Question')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_question_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
