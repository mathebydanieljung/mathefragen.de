from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from mathefragen.apps.guardian.models import (
    ReportedQuestion,
    ReportedAnswer,
    ReportedPlaylist
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        this_time_yesterday = timezone.now() - timezone.timedelta(days=1)

        reported_questions = ReportedQuestion.objects.filter(idate__gte=this_time_yesterday)
        reported_answers = ReportedAnswer.objects.filter(idate__gte=this_time_yesterday)
        reported_playlists = ReportedPlaylist.objects.filter(idate__gte=this_time_yesterday)

        number_reports = 0
        html_message = '<p>'
        for idx, r in enumerate(reported_questions):
            if not idx:
                html_message += '<b>Gemeldete Fragen:</b> <br>'
            html_message += '<p>' \
                            '<a href="https://%s%s">%s</a> <br> gemeldet am: %s <br> Hier <a href="%s">Admin-Link</a>' \
                            '</p>' % (
                                settings.DOMAIN,
                                r.question.get_absolute_url(),
                                r.question.title,
                                str(r.idate),
                                r.question.get_absolute_admin_url()
                            )
            number_reports += 1

        html_message += '</p><p>'

        for idx, a in enumerate(reported_answers):
            if not idx:
                html_message += '<b>Gemeldete Antworten:</b> <br>'
            html_message += '<p>' \
                            '<a href="https://%s%s">%s</a> <br> gemeldet am: %s <br> Hier <a href="%s">Admin-Link</a>' \
                            '</p>' % (
                                settings.DOMAIN,
                                a.answer.get_absolute_url(),
                                'Antwort',
                                str(a.idate),
                                a.answer.get_absolute_admin_url()
                            )
            number_reports += 1

        html_message += '</p></p>'

        for idx, pl in enumerate(reported_playlists):
            if not idx:
                html_message += '<b>Gemeldete Playlisten:</b> <br>'
            html_message += '<p>' \
                            '<a href="https://%s%s">%s</a> <br> gemeldet am: %s <br> Hier <a href="%s">Admin-Link</a> ' \
                            '</p>' % (
                                settings.DOMAIN,
                                pl.playlist.get_absolute_url(),
                                pl.playlist.name,
                                str(pl.idate),
                                pl.playlist.get_absolute_admin_url()
                            )
            number_reports += 1

        html_message += '</p>'

        if number_reports:
            send_mail(
                '%s Meldungen seit gestern auf %s' % (number_reports, settings.DOMAIN),
                message='',
                from_email='no-reply@mathefragen.de',
                recipient_list=settings.ADMINS_TO_REPORT,
                html_message=html_message
            )
