# Generated by Django 2.1.1 on 2020-08-05 19:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mathefragen.apps.core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('text', models.TextField()),
                ('accepted', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnswerComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('text', models.TextField()),
                ('answer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answer_comments', to='question.Answer')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_answer_comments', to=settings.AUTH_USER_MODEL)),
                ('soft_deleted', models.BooleanField(default=False)),
                ('source_ip', models.GenericIPAddressField(default='192.168.0.1')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('title', models.CharField(max_length=200)),
                ('text', models.TextField()),
                ('answered', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_questions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('text', models.TextField()),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_comments', to='question.Question')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_question_comments', to=settings.AUTH_USER_MODEL)),
                ('soft_deleted', models.BooleanField(default=False)),
                ('source_ip', models.GenericIPAddressField(default='192.168.0.1')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_answers', to='question.Question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_answers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='question',
            name='points',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='question',
            name='followers',
            field=models.ManyToManyField(related_name='followed_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='question',
            name='wp_post_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='answer',
            name='wp_post_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='views',
            field=models.IntegerField(default=0),
        ),
        migrations.RemoveField(
            model_name='answer',
            name='accepted',
        ),
        migrations.AddField(
            model_name='answer',
            name='accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.RemoveField(
            model_name='question',
            name='answered',
        ),
        migrations.AddField(
            model_name='question',
            name='wp_slug',
            field=models.CharField(default='', max_length=300),
        ),
        migrations.AddField(
            model_name='question',
            name='device',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='question',
            name='anonymous',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='closed',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='AnswerRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30)),
                ('idate', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('udate', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('youtube_id', models.CharField(default='', max_length=20)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_recommendations', to='question.Answer')),
                ('soft_deleted', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='answer',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterField(
            model_name='question',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_answers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='QuestionInvolvedUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='involved_peeps', to='question.Question')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='rank_date',
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='rank_reason',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='question',
            name='last_acted_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_acted_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='answer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='question',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('question', 'Question'), ('article', 'Article')], default='question', max_length=20),
        ),
        migrations.RemoveField(
            model_name='question',
            name='wp_slug',
        ),
        migrations.AlterField(
            model_name='answer',
            name='idate',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='question',
            name='idate',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at'),
        ),
        migrations.AddField(
            model_name='answer',
            name='vote_points',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='question',
            name='vote_points',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_answers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='question',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='question',
            name='source_ip',
            field=models.GenericIPAddressField(default='192.168.0.1'),
        ),
        migrations.AlterField(
            model_name='question',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='question',
            name='number_answers',
            field=models.IntegerField(blank=True, db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='question',
            name='closed',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='answer',
            name='hash_id',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30),
        ),
        migrations.AlterField(
            model_name='question',
            name='hash_id',
            field=models.CharField(db_index=True, default=mathefragen.apps.core.models.create_default_hash, editable=False, max_length=30),
        ),
        migrations.AddField(
            model_name='answer',
            name='soft_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='soft_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='edited_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='edited_questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='answer',
            name='source_ip',
            field=models.GenericIPAddressField(default='192.168.0.1'),
        ),
        migrations.AddField(
            model_name='answer',
            name='grasp_level',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name='question',
            name='wp_post_id',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='wp_post_id',
        ),
    ]
