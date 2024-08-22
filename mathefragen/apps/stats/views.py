import json
import datetime

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from django.shortcuts import HttpResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q

from mathefragen.apps.question.models import (
    Question,
    Answer,
    QuestionComment,
    AnswerComment
)
from mathefragen.apps.tutoring.models import HelpRequest
from mathefragen.apps.video.models import Video
from mathefragen.apps.review.models import UserReview
from mathefragen.apps.user.models import Profile


@api_view(['GET'])
@permission_classes((AllowAny, ))
def deeper_stats(request):
    """
    This API returns some stats payload for time-ranged stats,
    depending on the given range parameter.
    :param request:
    :return:
    {
        "percentage_answers": 95,
        "questions_num": 1233,
        "answers_num": 22323,
        "comments_num": 33434,
        "top_3_helpers": [
            {"username": "john", "url": "get_absolute_url", "verified": True, "answers": 223},
            {"username": "jamie", "url": "get_absolute_url", "verified": False, "answers": 213},
            {"username": "peter", "url": "get_absolute_url", "verified": True, "answers": 223}
        ],
        "top_3_questions": [
            {"title": "Question title 1", "url": "get_absolute_url", "answers": 123, "views": 2233},
            {"title": "Question title 2", "url": "get_absolute_url", "answers": 1243, "views": 3423},
            {"title": "Question title 3", "url": "get_absolute_url", "answers": 1123, "views": 4534}
        ]
    }
    """
    time_range = request.GET.get('range', '30')

    response_payload = {
        "questions_num": 0,
        "answers_num": 0,
        "percentage_answers": 0,
        "comments_num": 0,
        "top_3_helpers": list(),
        "top_3_questions": list()
    }

    since_date = timezone.now() - timezone.timedelta(days=30)
    if time_range == '7':
        since_date = timezone.now() - timezone.timedelta(days=7)
    elif time_range.lower() == 'total':
        since_date = datetime.datetime(1970, 1, 1, 0, 0)

    questions_num = Question.objects.filter(idate__gte=since_date).count()
    answers_num = Answer.objects.filter(idate__gte=since_date).count()

    response_payload['questions_num'] = questions_num
    response_payload['answers_num'] = answers_num

    ans_comments = AnswerComment.objects.filter(idate__gte=since_date).count()
    question_comments = QuestionComment.objects.filter(idate__gte=since_date).count()
    response_payload['comments_num'] = ans_comments + question_comments

    answered_questions = Question.objects.filter(
        Q(number_answers__gte=1) | Q(closed=True),
        idate__gte=since_date
    ).count()

    if questions_num:
        percent_answered = answered_questions * 100 / questions_num
        response_payload['percentage_answers'] = percent_answered
    else:
        response_payload['percentage_answers'] = 0

    top_3_questions = Question.objects.filter(
        idate__gte=since_date, vote_points__gte=1
    ).order_by('-vote_points')[:3]

    for q in top_3_questions:
        q_dict = {
            "title": q.title,
            "url": q.get_absolute_url(),
            "answers": q.number_answers,
            "views": q.views
        }
        response_payload['top_3_questions'].append(q_dict)

    top_3_helper_ids = Profile.get_helper_ids(
        from_date=since_date, to_date=timezone.now(), slice_number=3
    )
    top_3_helpers = User.objects.filter(id__in=top_3_helper_ids)
    for u in top_3_helpers:
        helper_dict = {
            "username": u.username,
            "url": u.profile.get_absolute_url(),
            "verified": u.profile.verified,
            "answers": u.profile.number_helps_since(date=since_date)
        }
        response_payload['top_3_helpers'].append(helper_dict)

    return HttpResponse(json.dumps(response_payload), content_type='application/json')


@api_view(['GET'])
@permission_classes((AllowAny, ))
def total_numbers(request):

    response_payload = {
        'questions': Question.objects.count(),
        'answers': Answer.objects.count(),
        'users': User.objects.count(),
        'unanswered_questions': Question.objects.filter(
            number_answers__lt=1,
            type='question',
            is_active=True,
            closed=False,
            soft_deleted=False
        ).count(),
        'reviews': UserReview.objects.count(),
        'videos': Video.objects.count(),
        'tutoring_sessions': HelpRequest.objects.count()
    }

    return HttpResponse(json.dumps(response_payload), content_type='application/json')
