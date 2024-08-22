from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from mathefragen.apps.review.api.serializers import (
    UserReviewSerializer
)
from mathefragen.apps.review.models import UserReview


@api_view(['GET'])
@permission_classes((AllowAny,))
def top_reviews(request):

    user_reviews = UserReview.objects.filter(is_happy=True)[:6]
    serializer = UserReviewSerializer(user_reviews, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

