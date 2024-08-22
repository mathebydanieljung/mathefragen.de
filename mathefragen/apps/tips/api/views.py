from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response

from mathefragen.apps.tips.models import PromotionBanner


@api_view(['GET'])
@permission_classes((AllowAny, ))
def promotion(request):

    promotion_banner = PromotionBanner.objects.filter(is_active=True).last()

    if not promotion_banner:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    response_payload = {
        'bg_color': promotion_banner.background_color,
        'text': promotion_banner.text,
        'text_color': promotion_banner.text_color,
        'link': promotion_banner.link,
    }

    return Response(response_payload, status=status.HTTP_200_OK)
