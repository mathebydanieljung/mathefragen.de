import re

from django.contrib.auth.models import User
from django.utils.html import strip_tags

from mathefragen.apps.core.utils import send_email_in_template


NOTIFICATION_EMAIL_SUBJECT = "Ein neuer Kommentar bei mathefragen.de"
NOTIFICATION_EMAIL_TEXT = "<p>Es gibt einen neuen Kommentar, indem du erwähnt wurdest.</p>"
NOTIFICATION_EMAIL_BUTTON_TEXT = "Jetzt öffnen"


class EmailNotifier(object):
    """
    it takes any text as input, searches for @text
    and notifies the user via email/push (depending on settings)
    """

    def __init__(self, text='', link=''):
        self.text = strip_tags(text).replace('&nbsp;', '')
        self.link = link

    def _extract_usernames(self):
        pattern = r'@(.*?\s)'
        matched_usernames = re.findall(pattern, self.text)
        matched_usernames = [username.strip().lower() for username in matched_usernames]
        return matched_usernames

    def _notify_user(self, user_emails):
        send_email_in_template(
            NOTIFICATION_EMAIL_SUBJECT,
            user_emails,
            **{
                'text': NOTIFICATION_EMAIL_TEXT,
                'link': self.link,
                'link_name': NOTIFICATION_EMAIL_BUTTON_TEXT
            }
        )

    def digest(self):
        found_usernames = self._extract_usernames()
        user_emails = []

        for username in found_usernames:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                continue
            user_emails.append(user.email)

        self._notify_user(user_emails=user_emails)

