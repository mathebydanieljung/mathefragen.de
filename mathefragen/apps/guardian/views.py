import json

from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required

from mathefragen.apps.question.models import Question, Answer
from mathefragen.apps.playlist.models import Playlist
from mathefragen.apps.guardian.models import (
    ReportedAnswer,
    ReportedQuestion,
    ReportedPlaylist,
    BlockedIP
)


@login_required
def report_content(request):
    object_id = request.POST.get('object_id')
    object_type = request.POST.get('object_type')
    report_reason = request.POST.get('report_reason')
    user = request.user

    bad_reasons = ['spam', 'rude_abusive']

    if object_type == 'question':
        question = Question.objects.get(id=object_id)

        ReportedQuestion.objects.create(
            reported_by_id=user.id, reason=report_reason, question_id=object_id
        )

        if user.profile.badges.filter(power_report=True).count():
            question.make_inactive()
        elif question.question_reports.count() >= 3:
            question.make_inactive()

        # deactivate user if reached
        if question.user and report_reason in bad_reasons:

            if user.profile.badges.filter(power_report=True).count():
                moderator = user.username
                question.user.profile.reported = 3
                question.user.profile.save()
            else:
                question.user.profile.increase_reports()

            # if blocked, then put content IP into BlockedIP
            if question.user.profile.reported >= 3 and question.source_ip:
                if not BlockedIP.objects.filter(ip=question.source_ip).count():
                    BlockedIP.objects.create(ip=question.source_ip)

        question.refresh_from_db()
        report_counts = question.question_reports.count()

    elif object_type == 'playlist':
        playlist = Playlist.objects.get(id=object_id)

        ReportedPlaylist.objects.create(
            reported_by_id=user.id, reason=report_reason, playlist_id=object_id
        )

        if playlist.playlist_reports.count() >= 3:
            playlist.make_inactive()

        # deactivate user if reached
        if playlist.user:
            playlist.user.profile.increase_reports()

        playlist.refresh_from_db()
        report_counts = playlist.playlist_reports.count()

    else:
        answer = Answer.objects.get(id=object_id)

        ReportedAnswer.objects.create(
            reported_by_id=user.id, reason=report_reason, answer_id=object_id
        )

        if user.profile.badges.filter(power_report=True).count():
            moderator = user.username
            answer.make_inactive()
        elif answer.answer_reports.count() >= 3:
            answer.make_inactive()

        # deactivate user if reached
        if answer.user and report_reason in bad_reasons:

            if user.profile.badges.filter(power_report=True).count():
                answer.user.profile.reported = 3
                answer.user.profile.save()
            else:
                answer.user.profile.increase_reports()

            # if blocked, then put content IP into BlockedIP
            if answer.user.profile.reported >= 3 and answer.source_ip:
                if not BlockedIP.objects.filter(ip=answer.source_ip).count():
                    BlockedIP.objects.create(ip=answer.source_ip)

        answer.refresh_from_db()
        report_counts = answer.answer_reports.count()

    return HttpResponse(json.dumps({
        'report_counts': report_counts
    }), content_type='application/json')

