import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes((AllowAny,))
def video_search(request):
    data = video_search_request(request.GET.get("q"))

    response = Response({
        'status': 'OK',
        'data': data
    }, status=status.HTTP_200_OK, headers={
        "Content-Security-Policy": "video-src 'self' 'unsafe-inline'  blob: data:  'unsafe-eval';",
    })

    return response


def video_search_request(q: str) -> dict:
    """
    Search for videos in the AIEDN API.
    """
    url = settings.AIEDN_API_URL + '/videos'
    headers = {
        'Authorization': f"Bearer {settings.AIEDN_API_TOKEN}",
    }

    files = {'search': q}

    return requests.request("POST", url, headers=headers, files=files).json()
