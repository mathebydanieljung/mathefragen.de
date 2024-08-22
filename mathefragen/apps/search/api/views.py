from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q
from django.contrib.auth.models import User

from mathefragen.apps.question.models import Question
from mathefragen.apps.question.api.serializers import QuestionSerializer
from mathefragen.apps.user.api.serializers import ProfileSerializer


@api_view(['GET'])
@permission_classes((AllowAny, ))
def search(request):

    search_term = request.GET.get('q')
    search_type = request.GET.get('type')

    if not search_term.strip():
        return Response({
            'msg': 'OK'
        }, status=status.HTTP_204_NO_CONTENT)

    search_term = search_term.lower()

    if search_type == 'question':
        questions = Question.objects.filter(
            Q(title__icontains=search_term) | Q(text__icontains=search_term)
        ).order_by('title')

        paginator = PageNumberPagination()
        paginator.page_size = 10
        questions_ = paginator.paginate_queryset(questions, request)

        serializer = QuestionSerializer(questions_, many=True)

        return paginator.get_paginated_response(serializer.data)

    elif search_type == 'user':
        users = User.objects.filter(
            username__icontains=search_term
        ).order_by('id')

        paginator = PageNumberPagination()
        paginator.page_size = 20
        users = paginator.paginate_queryset(users, request)

        profiles = [u.profile for u in users]
        serializer = ProfileSerializer(profiles, many=True)

        return paginator.get_paginated_response(serializer.data)

    return Response({'msg': 'no param ?type= is given'}, status=status.HTTP_400_BAD_REQUEST)
