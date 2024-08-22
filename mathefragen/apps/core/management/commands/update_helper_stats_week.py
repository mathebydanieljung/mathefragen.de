from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from mathefragen.apps.core.utils import send_email_in_template
from mathefragen.apps.user.models import Profile


class Command(BaseCommand):

    def handle(self, *args, **options):
        counter = 0
        this_week_in_calendar = timezone.now().isocalendar()[1]

        # only profiles, which did not answer this week, because profiles who answered this week already got updated
        for profile in Profile.objects.exclude(answered_week=this_week_in_calendar):
            profile.update_number_answers(counter=0)
            counter += 1

        send_email_in_template(
            '%s profile wurden auf weekly stats geupdated' % counter,
            settings.ADMINS_TO_REPORT,
            **{
                'text': '%s profile wurden auf weekly stats geupdated' % counter
            }
        )
