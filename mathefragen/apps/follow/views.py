import json

from django.shortcuts import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from mathefragen.apps.question.models import Question
from mathefragen.apps.hashtag.models import HashTag


@login_required
def follow_user(request):
    follower = request.user
    user_to_follow = request.GET.get('user_to_follow')

    if not user_to_follow:
        return HttpResponse(json.dumps({'status': 'no_one_to_follow'}), content_type='application/json')

    user_to_follow = User.objects.get(id=user_to_follow)
    if not follower.following_users.filter(following_id=user_to_follow.id).count():
        follower.following_users.create(
            following_id=user_to_follow.id
        )
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_following'}), content_type='application/json')


@login_required
def unfollow_user(request):
    follower = request.user
    user_to_unfollow = request.GET.get('user_to_unfollow')

    if not user_to_unfollow:
        return HttpResponse(json.dumps({'status': 'no_one_to_unfollow'}), content_type='application/json')

    user_to_unfollow = User.objects.get(id=user_to_unfollow)
    if follower.following_users.filter(following_id=user_to_unfollow.id).count():
        follower.following_users.filter(
            following_id=user_to_unfollow.id
        ).delete()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_unfollowing'}), content_type='application/json')


@login_required
def follow_question(request):
    follower = request.user
    question_to_follow = request.GET.get('question')

    if not question_to_follow:
        return HttpResponse(json.dumps({'status': 'no_question_to_follow'}), content_type='application/json')

    question_to_follow = Question.objects.get(id=question_to_follow)
    if not follower.following_questions.filter(question_id=question_to_follow.id).count():
        follower.following_questions.create(
            question_id=question_to_follow.id
        )
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_following'}), content_type='application/json')


@login_required
def unfollow_question(request):
    follower = request.user
    question_to_unfollow = request.GET.get('question')

    if not question_to_unfollow:
        return HttpResponse(json.dumps({'status': 'no_question_to_unfollow'}), content_type='application/json')

    question_to_unfollow = Question.objects.get(id=question_to_unfollow)
    if follower.following_questions.filter(question_id=question_to_unfollow.id).count():
        follower.following_questions.filter(
            question_id=question_to_unfollow.id
        ).delete()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_unfollowing'}), content_type='application/json')


@login_required
def follow_hashtag(request):
    follower = request.user
    hashtag_to_follow = request.GET.get('hashtag_to_follow')

    if not hashtag_to_follow:
        return HttpResponse(json.dumps({'status': 'no_hashtag_to_follow'}), content_type='application/json')

    hashtag_to_follow = HashTag.objects.get(id=hashtag_to_follow)
    if not follower.following_hashtags.filter(hashtag_id=hashtag_to_follow.id).count():
        follower.following_hashtags.create(
            hashtag_id=hashtag_to_follow.id
        )
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_following'}), content_type='application/json')


@login_required
def unfollow_hashtag(request):
    follower = request.user
    hashtag_to_unfollow = request.GET.get('hashtag_to_unfollow')

    if not hashtag_to_unfollow:
        return HttpResponse(json.dumps({'status': 'no_hashtag_to_unfollow'}), content_type='application/json')

    hashtag_to_unfollow = HashTag.objects.get(id=hashtag_to_unfollow)
    if follower.following_hashtags.filter(hashtag_id=hashtag_to_unfollow.id).count():
        follower.following_hashtags.filter(
            hashtag_id=hashtag_to_unfollow.id
        ).delete()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'already_unfollowing'}), content_type='application/json')
