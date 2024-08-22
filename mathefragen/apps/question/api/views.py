from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from mathefragen.apps.core.utils import create_default_hash
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.question.api.serializers import (
    QuestionSerializer,
    HotQuestionSerializer,
    CreateQuestionSerializer,
    AnswerSerializer,
    CreateAnswerSerializer,
    AnswerCommentSerializer,
    CreateAnswerCommentSerializer,
    QuestionCommentSerializer,
    CreateCommentSerializer,
    AnswerUpdateSerializer,
    ImageSerializer
)
from mathefragen.apps.question.models import (
    Question,
    QuestionComment,
    Answer,
    AnswerComment
)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def hottest_questions(request):
    """
    :return: currently only 1 hottest question, in future more.
    """
    two_weeks_ago = timezone.now() - timezone.timedelta(weeks=2)
    questions = Question.objects.filter(idate__gte=two_weeks_ago)
    if questions:
        questions = questions.order_by('?')[:2]
        serializer_data = HotQuestionSerializer(questions, many=True, context={'request': request}).data
        return Response(serializer_data, status=status.HTTP_200_OK)

    return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def questions_list(request):
    questions_ = Question.objects.order_by('-rank_date')

    user_id = request.GET.get('user', 'no_user_id')
    hashtag = request.GET.get('hashtag', '')
    cut = request.GET.get('cut', 'no_cut')
    question_type = request.GET.get('type', '')
    question_ids = request.GET.get('ids', '')
    paginated = request.GET.get('paginated', '')

    sort_by = request.GET.get('sort_by', '')

    if sort_by == 'views':
        questions_ = questions_.order_by('-views')

    if sort_by == 'points':
        questions_ = questions_.order_by('-points')

    if sort_by == 'answers':
        questions_ = questions_.annotate(answers=Count('question_answers')).order_by('-answers')

    if question_ids:
        splitted_question_ids = None
        try:
            splitted_question_ids = [int(qid) for qid in question_ids.split(',') if qid]
        except Exception:
            pass

        if splitted_question_ids:
            questions_ = questions_.filter(id__in=splitted_question_ids)

    if user_id.isdigit():
        try:
            _ = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                'msg': 'this user id [%s] is not in db :/' % user_id
            }, status=status.HTTP_400_BAD_REQUEST)

        questions_ = questions_.filter(user_id=user_id)

    if hashtag:
        hashtag_obj = HashTag.objects.filter(name=hashtag).last()
        if hashtag_obj:
            questions_ = questions_.filter(id__in=list(hashtag_obj.questions.values_list('id', flat=True)))

    if cut.isdigit():
        cut = int(cut)
        questions_ = questions_.order_by('-id')[:cut]

    if question_type == 'unanswered':
        questions_ = questions_.annotate(answers=Count('question_answers')).filter(answers__lt=1)

    if question_type == 'answered':
        questions_ = questions_.annotate(answers=Count('question_answers')).filter(answers__gt=0)

    if question_type == 'new':
        questions_ = questions_.annotate(answers=Count('question_answers')).filter(
            answers__lt=1, idate__gte=(timezone.now() - timezone.timedelta(hours=20))
        )

    if paginated == 'yes':
        serializer_data = QuestionSerializer(questions_, many=True, context={'request': request}).data
        response_data = Response(serializer_data, status=status.HTTP_200_OK)

    else:
        paginator = PageNumberPagination()
        paginator.page_size = 10
        questions_ = paginator.paginate_queryset(questions_, request)

        serializer_data = QuestionSerializer(questions_, many=True, context={'request': request}).data
        response_data = paginator.get_paginated_response(serializer_data)

    return response_data


@api_view(['GET'])
@permission_classes((AllowAny, ))
@authentication_classes((JWTAuthentication,))
def question_detail(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    question.increase_views_counter(request=request)

    return Response(QuestionSerializer(question, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def question_put(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = QuestionSerializer(question, data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()

        question.re_rank(reason='geändert', last_acted_user=request.user)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def question_delete(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.id != question.user_id:
        return Response({'msg': 'not yours'}, status=status.HTTP_403_FORBIDDEN)

    if question.user.profile.total_questions >= 1:
        question.user.profile.total_questions -= 1
        question.user.profile.save()

    question.delete()

    # update stats
    stats = request.stats
    if stats:
        stats.update_total_questions()

    return Response({'msg': 'success'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def create_question(request):

    if request.method == 'POST':
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            question.repair_images()

            if not question.user.profile.number_asks:
                question.is_first_question = True
                question.save()

            question.user.profile.number_asks += 1
            question.user.profile.save()

            # update stats
            stats = request.stats
            if stats:
                stats.update_total_questions()

            question.re_rank(reason='gefragt', last_acted_user=question.user)

            return Response(QuestionSerializer(question, context={'request': request}).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def upload_image(request):

    media_file_serializer = ImageSerializer(data=request.data)
    if media_file_serializer.is_valid():
        uploaded_file = media_file_serializer.validated_data.get('media_file')
        if not uploaded_file:
            return Response({'location': ''})

        date_folder = '%s/%s/%s/' % (
            timezone.now().year, timezone.now().month, timezone.now().day
        )
        filename = '%s.%s' % (create_default_hash(length=12), uploaded_file.name.split('.')[-1])
        final_path = '%s%s' % (
            date_folder, filename
        )

        # dont eat up memory if file is too big
        with default_storage.open(final_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        file_path = 'https://media.mathefragen.de/media/%s%s' % (date_folder, filename)

        return Response({
            'location': file_path
        })

    return Response(media_file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def answers_list(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    all_answers_ = Answer.objects.filter(question_id=question.id).order_by('id')

    user_id = request.GET.get('user', 'no_user_id')
    answer_ids = request.GET.get('ids', '')

    if answer_ids:
        splitted_answer_ids = None
        try:
            splitted_answer_ids = [int(aid) for aid in answer_ids.split(',') if aid]
        except Exception:
            pass

        if splitted_answer_ids:
            all_answers_ = all_answers_.filter(id__in=splitted_answer_ids)

    if user_id.isdigit():
        try:
            _ = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                'msg': 'this user id [%s] is not in db :/' % user_id
            }, status=status.HTTP_400_BAD_REQUEST)

        all_answers_ = all_answers_.filter(user_id=user_id)

    return Response(AnswerSerializer(all_answers_, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def all_answers_list(request):

    all_answers_ = Answer.objects.all().order_by('id')

    user_id = request.GET.get('user', 'no_user_id')
    answer_ids = request.GET.get('ids', '')

    if answer_ids:
        splitted_answer_ids = None
        try:
            splitted_answer_ids = [int(aid) for aid in answer_ids.split(',') if aid]
        except Exception:
            pass

        if splitted_answer_ids:
            all_answers_ = all_answers_.filter(id__in=splitted_answer_ids)

    if user_id.isdigit():
        try:
            _ = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                'msg': 'this user id [%s] is not in db :/' % user_id
            }, status=status.HTTP_400_BAD_REQUEST)

        all_answers_ = all_answers_.filter(user_id=user_id)

    return Response(AnswerSerializer(all_answers_, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def create_answer(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        serializer = CreateAnswerSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.save()
            answer.question = question
            answer.save()

            answer.user.profile.update_number_answers(question_id=question_id)

            # update helped tags
            answer.user.profile.update_most_helped_tags()
            # update number of answers on the question
            question.sync_number_answers()

            # update stats
            stats = request.stats
            if stats:
                stats.update_total_answers()

            question.inform_questioner(answer=answer)

            question.re_rank(reason='beantwortet', last_acted_user=answer.user)

            return Response(AnswerSerializer(answer, context={'request': request}).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def answer_detail(request, question_id, answer_id):
    try:
        _ = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(AnswerSerializer(answer, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def answer_put(request, question_id, answer_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = AnswerUpdateSerializer(answer, data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()

        question.re_rank(reason='Antwort geändert', last_acted_user=answer.user)

        return Response(AnswerSerializer(answer, context={'request': request}).data, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def accept_answer(request, question_id, answer_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response({
            'msg': 'question not found'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response({
            'msg': 'answer not found'
        }, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if question.user_id != user.id:
        return Response({'msg': 'not_allowed_to_accept'}, status=status.HTTP_403_FORBIDDEN)

    answer.set_accepted()

    # question.re_rank(reason='Antwort akzeptiert', last_acted_user=answer.user)

    # give points to user who answered
    user_who_answered = answer.user.profile
    user_who_answered.increase_points(points=15, reason='helped')

    # give 2 credits because he accepted
    user.profile.increase_points(points=2, reason='accepted')

    return Response({'msg': 'success'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def answer_delete(request, question_id, answer_id):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.id != answer.user_id:
        return Response({'msg': 'not yours'}, status=status.HTTP_403_FORBIDDEN)

    profile = answer.user.profile
    answer.delete()

    profile.update_number_answers(counter=-1)
    profile.update_most_helped_tags()
    question.sync_number_answers()

    # update stats
    stats = request.stats
    if stats:
        stats.update_total_answers()

    return Response({'msg': 'success'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def create_question_comment(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CreateCommentSerializer(data=request.data)
    if serializer.is_valid():
        comment = serializer.save()
        comment.question = question
        comment.save()

        question.re_rank(reason='kommentiert', last_acted_user=comment.user)

        return Response(QuestionCommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def question_comments_list(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    all_comments_ = QuestionComment.objects.filter(question_id=question.id).order_by('idate')
    return Response(QuestionCommentSerializer(all_comments_, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def question_comment_detail(request, question_id, comment_id):
    try:
        _ = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        comment = QuestionComment.objects.get(pk=comment_id)
    except QuestionComment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(QuestionCommentSerializer(comment, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def question_comment_put(request, question_id, comment_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        comment = QuestionComment.objects.get(pk=comment_id)
    except QuestionComment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CreateCommentSerializer(comment, data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()

        question.re_rank(reason='kommentiert', last_acted_user=comment.user)

        return Response(QuestionCommentSerializer(comment, context={'request': request}).data, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def question_comment_delete(request, question_id, comment_id):
    try:
        _ = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        comment = QuestionComment.objects.get(pk=comment_id)
    except QuestionComment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.id != comment.user_id:
        return Response({'msg': 'not yours'}, status=status.HTTP_403_FORBIDDEN)

    comment.delete()

    return Response({'msg': 'success'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def create_answer_comment(request, answer_id):
    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CreateAnswerCommentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        answer_comment = serializer.save()
        answer_comment.answer = answer
        answer_comment.save()

        answer.question.re_rank(reason='Antwort kommentiert', last_acted_user=answer_comment.user)

        return Response(AnswerCommentSerializer(answer_comment, context={'request': request}).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def answer_comments_list(request, answer_id):
    try:
        _ = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    all_answer_comments_ = AnswerComment.objects.filter(answer_id=answer_id).order_by('idate')
    return Response(AnswerCommentSerializer(all_answer_comments_, many=True, context={'request': request}).data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def answer_comment_put(request, answer_id, comment_id):
    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        comment = AnswerComment.objects.get(pk=comment_id)
    except AnswerComment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CreateAnswerCommentSerializer(comment, data=request.data, context={'request': request})
    if serializer.is_valid():
        updated_comment = serializer.save()

        answer.question.re_rank(reason='Antwort kommentiert', last_acted_user=comment.user)

        return Response(AnswerCommentSerializer(updated_comment, context={'request': request}).data, status=status.HTTP_204_NO_CONTENT)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def answer_comment_delete(request, answer_id, comment_id):
    try:
        _ = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        comment = AnswerComment.objects.get(pk=comment_id)
    except AnswerComment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.id != comment.user_id:
        return Response({'msg': 'not yours'}, status=status.HTTP_403_FORBIDDEN)

    comment.delete()

    return Response({'msg': 'success'}, status=status.HTTP_204_NO_CONTENT)
