from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User

from mathefragen.apps.tutoring.models import HelpRequest


class Command(BaseCommand):

    def handle(self, *args, **options):
        open_help_requests = HelpRequest.objects.filter(
            Q(tutor_completed_at__isnull=True) | Q(student_completed_at__isnull=True),
            tutor_joined_at__isnull=False,
            student_joined_at__isnull=False
        )
        for request in open_help_requests:
            # only if the request is in history incl. duration + buffer (20 hour)
            last_minute_of_session = (request.accepted_date_time + timezone.timedelta(minutes=request.duration))
            twenty_minutes_before = (timezone.now() - timezone.timedelta(minutes=20))

            if last_minute_of_session < twenty_minutes_before:
                if not request.tutor_completed_at:
                    request.tutor_completed_at = timezone.now()
                if not request.student_completed_at:
                    request.student_completed_at = timezone.now()

                request.save()

