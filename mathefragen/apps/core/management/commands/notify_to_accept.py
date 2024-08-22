from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from mathefragen.apps.core.utils import send_email_in_template
from mathefragen.apps.question.models import Question


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        this job looks for questions that are answered but its answers are not accepted yet.
        The Owners of those questions should be notified only once, so we:
        1. notify once every 3 days
        2. for the questions that are 3 days old.
        """
        three_days_ago = timezone.now() - timezone.timedelta(days=3)

        last_3_day_open_questions = Question.objects.filter(closed=False, idate__gte=three_days_ago)

        # filter out questions without answer
        for q in last_3_day_open_questions:
            if not q.question_answers.count():
                last_3_day_open_questions = last_3_day_open_questions.exclude(id=q.id)

        users_with_3_day_open_questions = list(
            set(list(last_3_day_open_questions.values_list('user_id', flat=True)))
        )

        for user_id in users_with_3_day_open_questions:

            user = User.objects.get(id=user_id)
            open_question_url = user.profile.get_open_questions_url()

            if user.email:
                send_email_in_template(
                    'Antworten warten auf dein Feedback',
                    [user.email],
                    **{
                        'text': 'Es gibt offene Antworten auf deine Fragen.'
                                '<p>Bitte markiere die Antwort als akzeptiert, die dir am meisten geholfen hat.</p>'
                                '<p>Damit zeigst du deine Dankbarkeit und hilfst den anderen.</p>',
                        'link_name': 'Jetzt meine offene Fragen zeigen',
                        'link': open_question_url
                    }
                )
