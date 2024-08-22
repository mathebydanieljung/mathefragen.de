from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.hashtag.api.serializers import HashTagSerializer


@api_view(['GET'])
@permission_classes((AllowAny, ))
def hashtag_search(request, hash_tag):

    direct_hashtags = HashTag.objects.filter(name__istartswith=hash_tag)
    containing_hashtags = HashTag.objects.filter(name__icontains=hash_tag)

    hashtags = direct_hashtags | containing_hashtags

    return Response(HashTagSerializer(hashtags, many=True).data, status=status.HTTP_200_OK)
