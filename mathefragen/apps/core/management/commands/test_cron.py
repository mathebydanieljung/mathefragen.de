from django.conf import settings
from django.core.management.base import BaseCommand

from mathefragen.apps.core.utils import send_email_in_template


class Command(BaseCommand):

    def handle(self, *args, **options):
        send_email_in_template(
            'test cron email',
            settings.ADMINS_TO_REPORT,
            **{
                'text': 'test cron email'
            }
        )
