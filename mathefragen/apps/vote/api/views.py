from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from mathefragen.apps.question.models import Question, Answer
from mathefragen.apps.vote.api.serializers import VoteSerializer
from mathefragen.apps.vote.models import Vote


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def vote_question(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return Response({
            'msg': 'question not found'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = VoteSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        created = serializer.save()

        question.vote_points = question.votes
        question.save(update_fields=['vote_points'])

        # give some points
        question_owner = question.user.profile
        question_owner.increase_points(points=5, reason='got_vote')

        data = serializer.data
        data['created'] = created
        data['new_votes'] = question.vote_points

        return Response(data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def vote_answer(request, answer_id):
    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        return Response({
            'msg': 'answer not found'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = VoteSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        created = serializer.save()

        answer.vote_points = answer.votes
        answer.save(update_fields=['vote_points'])

        # give some points
        answer_owner = answer.user.profile
        answer_owner.increase_points(points=5, reason='got_vote')

        data = serializer.data
        data['created'] = created
        data['new_votes'] = answer.vote_points

        return Response(data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def votes(request):
    """
    :param request:
    :return: votes, filtered by filters
    """

    all_votes = Vote.objects.all()

    user = request.GET.get('user', 'no_user_id')
    answer = request.GET.get('answer', 'no_answer_id')
    question = request.GET.get('question', 'no_question_id')

    if user.isdigit():
        all_votes = all_votes.filter(user_id=int(user))

    if answer.isdigit():
        all_votes = all_votes.filter(answer_id=int(answer))
    elif question.isdigit():
        all_votes = all_votes.filter(question_id=int(question))

    data = VoteSerializer(all_votes, many=True, context={'request': request}).data

    return Response(data, status=status.HTTP_200_OK)

