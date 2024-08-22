from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse

from mathefragen.apps.core.utils import send_email_in_template


def send_feedback(request):
    if request.user_agent.is_bot:
        return HttpResponse('sorry you are bot')

    feedback_text = request.POST.get('feedback_text')
    feedback_category = request.POST.get('feedback_category')
    path = request.POST.get('path')
    feedback_email = request.POST.get('feedback_email')

    if not feedback_email and request.user.is_authenticated:
        feedback_email = request.user.email

    send_email_in_template(
        'Feedback von mathefragen.de',
        settings.ADMINS_TO_REPORT,
        **{
            'text': 'Feedback %s: '
                    '<p>Kategorie: %s</p>'
                    '<p>Pfad: %s</p>'
                    '<p>Feedback: <br><br> "%s"</p><br>'
                    'META: <br><br>'
                    '<p>Browser: %s</p>'
                    '<p>OS: %s</p>'
                    '<p>Device: %s</p>' % (
                        'von %s' % feedback_email if feedback_email else '',
                        feedback_category,
                        path,
                        feedback_text,
                        request.user_agent.browser,
                        request.user_agent.os,
                        request.user_agent.device
                    )
        }
    )

    return HttpResponse('OK')


@login_required
def save_channel_suggestion(request):
    channel_suggestion_category = request.POST.get('channel_suggestion_category')
    channel_suggest_description = request.POST.get('channel_suggest_description')

    request.user.learntool_suggestions.create(
        type=channel_suggestion_category,
        description=channel_suggest_description
    )

    return HttpResponse('ok')
