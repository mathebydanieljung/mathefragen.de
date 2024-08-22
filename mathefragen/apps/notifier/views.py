from django.conf import settings
from django.contrib.auth.models import User
from pyfcm import FCMNotification
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import RefreshSerializer, PushSerializer


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def refresh(request):
    serializer = RefreshSerializer(data=request.data)
    if serializer.is_valid():
        user_id = serializer.data.get('user_id')

        user = User.objects.get(id=user_id)

        user.profile.fcm_token = serializer.data.get('fcm_token')
        user.profile.save(update_fields=['fcm_token'])

        return Response({
            'status': 'OK'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def push(request):
    serializer = PushSerializer(data=request.data)
    if serializer.is_valid():
        to_user_id = serializer.data.get('to_user_id')
        question_id = serializer.data.get('question_id')

        user = User.objects.get(id=to_user_id)

        fcm_token = user.profile.fcm_token

        push_service = FCMNotification(api_key=settings.FIREBASE_SERVER_KEY)

        push_service.notify_single_device(
            registration_id=fcm_token,
            message_title='Jemand braucht deine Hilfe!',
            message_body='Klick hier, um die Frage zu sehen',
            data_message={
                'to_user_id': to_user_id,
                'question_id': question_id,
            }
        )
        return Response({
            'status': 'OK'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
