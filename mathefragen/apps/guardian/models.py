from django.db import models
from django.contrib.auth.models import User

from mathefragen.apps.core.models import Base
from mathefragen.apps.playlist.models import Playlist
from mathefragen.apps.question.models import Answer, Question


QUESTION_REPORT_TYPES = (
    ('spam', 'Besteht nur, um ein Produkt oder eine Dienstleistung zu bewerben'),
    ('rude_abusive', 'Eine vernünftige Person würde diesen Inhalt für einen '
                     'respektvollen Diskurs ungeeignet finden.'),
    ('general', 'Diese Frage ist völlig unklar, unvollständig, '
                'übermäßig breit und es ist unwahrscheinlich, '
                'dass sie über die Bearbeitung behoben werden.'),
    ('duplicate', 'Diese Frage wurde bereits gestellt und hat bereits eine Antwort.'),
    ('bad_quality', 'Diese Frage hat schwerwiegende Formatierungs- oder Inhaltsprobleme. Es ist unwahrscheinlich, '
                    'dass diese Frage durch die Bearbeitung zu retten ist und möglicherweise entfernt werden muss.'),
    ('need_moderator_attention', 'Ein Problem, das oben nicht aufgeführt ist, '
                                 'erfordert die Reaktion eines Moderators.'),
    ('incomplete', 'Diese Frage hat lückenhafte Angaben.')
)

ANSWER_REPORT_TYPES = (
    ('spam', 'Besteht nur, um ein Produkt oder eine Dienstleistung zu bewerben'),
    ('rude_abusive', 'Eine vernünftige Person würde diesen Inhalt für einen '
                     'respektvollen Diskurs ungeeignet finden.'),
    ('general', 'Diese Antwort ist völlig unklar, unvollständig, '
                'übermäßig breit und es ist unwahrscheinlich, '
                'dass sie über die Bearbeitung behoben werden.'),
    ('duplicate', 'Diese Antwort ist überflüßig und möglicherweise ein Copy-Paste.'),
    ('bad_quality', 'Diese Antwort hat schwerwiegende Formatierungs- oder Inhaltsprobleme. Es ist unwahrscheinlich, '
                    'dass diese Antwort durch die Bearbeitung zu retten ist und möglicherweise entfernt werden muss.'),
    ('need_moderator_attention', 'Ein Problem, das oben nicht aufgeführt ist, '
                                 'erfordert die Reaktion eines Moderators.'),
    ('incomplete', 'Diese Antwort hat lückenhafte Angaben.')
)


class ReportedQuestion(Base):
    question = models.ForeignKey(
        Question,
        related_name='question_reports',
        on_delete=models.CASCADE
    )
    reported_by = models.ForeignKey(
        User,
        related_name='user_question_reports',
        on_delete=models.CASCADE
    )
    reason = models.CharField(
        max_length=50,
        choices=QUESTION_REPORT_TYPES,
        default='general'
    )


class ReportedAnswer(Base):
    answer = models.ForeignKey(
        Answer,
        related_name='answer_reports',
        on_delete=models.CASCADE
    )
    reported_by = models.ForeignKey(
        User,
        related_name='user_answer_reports',
        on_delete=models.CASCADE
    )
    reason = models.CharField(
        max_length=50,
        choices=ANSWER_REPORT_TYPES,
        default='general'
    )


class ReportedPlaylist(Base):
    playlist = models.ForeignKey(
        Playlist,
        related_name='playlist_reports',
        on_delete=models.CASCADE
    )
    reported_by = models.ForeignKey(
        User,
        related_name='user_playlist_reports',
        on_delete=models.CASCADE
    )
    reason = models.CharField(
        max_length=50,
        default='general'
    )


class BlockedIP(models.Model):
    ip = models.GenericIPAddressField(default='192.168.0.1', db_index=True)
    idate = models.DateTimeField(auto_now_add=True, verbose_name='created at')

    @classmethod
    def is_blocked(cls, ip):
        assert ip
        return cls.objects.filter(ip=ip).count() > 0

    def __str__(self):
        return 'blocked IP: %s' % self.ip
