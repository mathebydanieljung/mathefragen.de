from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

from .models import Answer
from mathefragen.apps.core.utils import send_email_in_template


@receiver(post_save, sender=Answer)
def detect_new_helpers(sender, **kwargs):
    answer = kwargs['instance']
    if kwargs['created']:

        profile = answer.user.profile

        is_due = not profile.helper_detected_at or profile.helper_detected_at < (timezone.now() - timezone.timedelta(days=7))  # noqa
        if profile.has_reached_helper_level() and not profile.verified and is_due and profile.is_energetic():
            send_email_in_template(
                "Ein neuer Helfer erkannt.",
                settings.ADMINS_TO_REPORT,
                **{
                    'text': 'Hey, Team.'
                            '<p>Das System hat einen neuen Helfer erkannt:</p>'
                            '<p>Profil: <a href="https://%s%s">%s</a></p>'
                            '<p>Admin-Link: <a href="https://%s%suser/profile/%s/change/">%s</a></p></p>'
                            % (
                                settings.DOMAIN,
                                profile.get_absolute_url(),
                                profile.user.username,
                                settings.DOMAIN,
                                settings.ADMIN_URL,
                                profile.id,
                                profile.user.username
                            )
                }
            )
            profile.helper_detected_at = timezone.now()
            profile.save()
