import json

from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Vote, CommentVote
from mathefragen.apps.question.models import Question, Answer, QuestionComment, AnswerComment
from mathefragen.apps.playlist.models import Playlist


@login_required
def vote_playlist(request, playlist_hash):
    user = request.user
    vote_type = request.POST.get('vote_type', 'up')

    playlist = Playlist.objects.get(hash_id=playlist_hash)

    if not playlist.user_id:
        # user is none.
        return HttpResponse(json.dumps({
            'created': False,
            'new_votes': playlist.votes
        }))

    if not playlist.user_id:
        return HttpResponse(json.dumps({
            'created': False,
            'new_votes': playlist.votes
        }))

    created = Vote.create_vote(**{
        'user': user,
        'playlist': playlist,
        'type': vote_type,
        'reason': ''
    })

    # give some points
    if created:
        new_point = 10
        if 'down' in vote_type:
            new_point = -10

        playlist.update_votes(new_points=new_point)

    return HttpResponse(json.dumps({
        'created': created,
        'new_votes': playlist.vote_points
    }))


@login_required
def undo_vote_playlist(request, playlist_hash):
    user = request.user

    playlist = Playlist.objects.get(hash_id=playlist_hash)
    if request.method == 'POST' and request.is_ajax():
        vote_type = request.POST.get('vote_type')
        if vote_type == 'down':
            Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='down').delete()
            playlist.update_votes(new_points=10)
        elif vote_type == 'up':
            Vote.objects.filter(user_id=user.id, playlist_id=playlist.id, type='up').delete()
            playlist.update_votes(new_points=-10)

    return HttpResponse(json.dumps({
        'new_votes': playlist.vote_points
    }))


@login_required
def vote_question(request, question_id):
    user = request.user
    vote_type = request.POST.get('vote_type', 'up')
    reason = request.POST.get('reason', '')

    question = Question.objects.get(id=question_id)

    if not question.user_id:
        return HttpResponse(json.dumps({
            'created': False,
            'new_votes': question.vote_points
        }))

    created = Vote.create_vote(**{
        'user': user,
        'question': question,
        'reason': reason,
        'type': vote_type
    })

    # give some points
    if created:
        new_point = 5
        if 'down' in vote_type:
            new_point = -5

        question.update_votes(new_points=new_point)

        if 'down' in vote_type:
            question.inform_about_downvote(reason=reason)

    return HttpResponse(json.dumps({
        'created': created,
        'new_votes': question.vote_points
    }))


@login_required
def undo_vote_question(request, question_id):
    user = request.user

    question = Question.objects.get(id=question_id)
    if request.method == 'POST' and request.is_ajax():
        vote_type = request.POST.get('vote_type')
        if vote_type == 'down':
            Vote.objects.filter(user_id=user.id, question_id=question_id, type='down').delete()
            question.update_votes(new_points=5)
        elif vote_type == 'up':
            Vote.objects.filter(user_id=user.id, question_id=question_id, type='up').delete()
            question.update_votes(new_points=-5)

    return HttpResponse(json.dumps({
        'new_votes': question.vote_points
    }))


@login_required
def vote_answer(request, answer_id):
    user = request.user
    vote_type = request.POST.get('vote_type', 'up')
    reason = request.POST.get('reason', '')
    answer = Answer.objects.get(id=answer_id)

    if not answer.user_id:
        return HttpResponse(json.dumps({
            'created': False,
            'new_votes': answer.vote_points
        }))

    created = Vote.create_vote(**{
        'user': user,
        'answer': answer,
        'reason': reason,
        'type': vote_type
    })

    # give some points
    if created:
        new_point = 5
        if 'down' in vote_type:
            new_point = -5

        answer.update_votes(new_points=new_point)

        if 'down' in vote_type:
            answer.inform_about_downvote(reason=reason)

    return HttpResponse(json.dumps({
        'created': created,
        'new_votes': answer.vote_points
    }))


@login_required
def undo_vote_answer(request, answer_id):
    user = request.user

    answer = Answer.objects.get(id=answer_id)
    if request.method == 'POST' and request.is_ajax():
        vote_type = request.POST.get('vote_type')
        if vote_type == 'down':
            Vote.objects.filter(user_id=user.id, answer_id=answer_id, type='down').delete()
            answer.update_votes(new_points=5)
        elif vote_type == 'up':
            Vote.objects.filter(user_id=user.id, answer_id=answer_id, type='up').delete()
            answer.update_votes(new_points=-5)

    return HttpResponse(json.dumps({
        'new_votes': answer.vote_points
    }))


@login_required
def vote_comment(request):
    comment_id = request.GET.get('comment_id')
    object_type = request.GET.get('ot')
    event_type = request.GET.get('et')
    if object_type == 'question':
        comment = QuestionComment.objects.get(id=comment_id)
        if event_type == 'add':
            CommentVote.objects.create(
                question_comment_id=comment_id,
                user_id=request.user.id
            )
            comment.vote_points += 1
            comment.save()
        else:
            CommentVote.objects.filter(question_comment_id=comment_id).delete()
            if comment.vote_points > 0:
                comment.vote_points -= 1
                comment.save()

    elif object_type == 'answer':
        comment = AnswerComment.objects.get(id=comment_id)
        if event_type == 'add':
            CommentVote.objects.create(
                answer_comment_id=comment_id,
                user_id=request.user.id
            )
            comment.vote_points += 1
            comment.save()
        else:
            CommentVote.objects.filter(answer_comment_id=comment_id).delete()
            if comment.vote_points > 0:
                comment.vote_points -= 1
                comment.save()

    if not comment.user_id:
        return HttpResponse(json.dumps({
            'created': False,
            'new_votes': comment.vote_points
        }))

    return HttpResponse(json.dumps({
        # todo: fix 'created' later
        'created': True,
        'new_votes': comment.vote_points
    }))


@login_required
def undo_vote_comment(request):
    comment_id = request.GET.get('comment_id')
    user = request.user
    vote_type = request.POST.get('vote_type', 'up')
    reason = request.POST.get('reason', '')
    return HttpResponse('okay')
