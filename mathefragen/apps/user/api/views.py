import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import reverse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from mathefragen.apps.core.utils import send_email_in_template, convert_base64_to_image, create_default_hash
from mathefragen.apps.question.models import Answer
from mathefragen.apps.user.api.serializers import (
    LoginSerializer,
    UserRegisterSerializer,
    EmailSerializer,
    UserImageSerializer,
    ProfileSerializer,
)


@extend_schema(
    parameters=[UserRegisterSerializer],
    request=UserRegisterSerializer,
    responses=ProfileSerializer
)
@api_view(['POST'])
@permission_classes((AllowAny,))
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        if serializer.validated_data.get('status'):
            user.profile.status = serializer.validated_data.get('status')
            user.profile.save()

        token = user.profile.generate_jwt_token()
        user.profile.last_active = timezone.now()
        user.profile.save()

        stats = request.stats
        if stats:
            stats.update_total_users()

        profile_data = ProfileSerializer(user.profile).data
        profile_data['token'] = token

        return Response(profile_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[LoginSerializer],
    request=LoginSerializer,
    responses=ProfileSerializer
)
@api_view(['POST'])
@permission_classes((AllowAny,))
def login_me(request):

    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.get_user()
        if not user:
            return Response({
                'msg': 'Bad request. Credentials are wrong.'
            }, status=status.HTTP_400_BAD_REQUEST)

        token = user.profile.generate_jwt_token()

        profile_data = ProfileSerializer(user.profile).data
        profile_data['token'] = token

        return Response(profile_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def send_pwd_reset_email(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.data.get('email').lower()
        try:
            user = User.objects.get(email=email)
        except:
            return Response({
                'msg': 'Email does not exist.'
            }, status=status.HTTP_400_BAD_REQUEST)

        pw_onetime_hash = create_default_hash(length=8)
        user.profile.pw_onetime_hash = pw_onetime_hash
        user.profile.save()

        password_reset_link = 'https://%s%s' % (
            settings.DOMAIN, reverse('set_password', kwargs={
                'pw_onetime_hash': pw_onetime_hash
            })
        )

        send_email_in_template(
            'Passwort zurücksetzen - mathefragen.de',
            [email],
            **{
                'text': '<p>Hier kannst du nun dein Passwort zurücksetzen. Bitte klicke hierzu den Button an: ',
                'link': password_reset_link,
                'link_name': 'Passwort zurücksetzen'
            }
        )

        return Response({
            'msg': 'OK'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
def top_helper(request):
    begin = request.GET.get('begin')
    end = request.GET.get('end')

    if not begin or not end:
        return Response({
            'msg': 'No time range given.'
        }, status=status.HTTP_400_BAD_REQUEST)

    begin = datetime.datetime.fromtimestamp(int(begin))
    end = datetime.datetime.fromtimestamp(int(end))

    answers_ids_between_this_time = list(
        Answer.objects.filter(idate__gte=begin, idate__lte=end).values_list('id', flat=True)
    )

    users = User.objects.filter(user_answers__id__in=answers_ids_between_this_time).annotate(
        number_answers=Count('user_answers')
    ).order_by('-number_answers')

    profiles = []
    for user in users:
        if hasattr(user, 'profile'):
            profiles.append(user.profile)

    serializer = ProfileSerializer(profiles, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny,))
def users_list(request):
    """
    User List API
    """
    users = User.objects.order_by('-profile__points')

    from_points = request.GET.get('from_points', 'no_from_points')
    sort_by = request.GET.get('sort_by', 'points')
    user_ids = request.GET.get('ids', '')
    username = request.GET.get('username', '')

    if sort_by == 'points':
        users = users.order_by('-profile__points')

    if username:
        users = users.filter(username__icontains=username)

    if from_points.isdigit():
        users = users.filter(profile__points__gte=from_points).order_by('-profile__points')

    if user_ids:
        splitted_user_ids = None
        try:
            splitted_user_ids = [int(uid) for uid in user_ids.split(',') if uid]
        except Exception:
            pass

        if splitted_user_ids:
            users = users.filter(id__in=splitted_user_ids)

    paginator = PageNumberPagination()
    paginator.page_size = 20
    users = paginator.paginate_queryset(users, request)

    profiles = [u.profile for u in users if hasattr(u, 'profile')]
    serializer = ProfileSerializer(profiles, many=True)

    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes((AllowAny,))
def user_detail_get(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(ProfileSerializer(user.profile).data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def user_detail_delete(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    user.delete()

    stats = request.stats
    if stats:
        stats.update_total_users()

    return Response({'msg': 'success'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE', 'GET', 'POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def user_image_change(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        serializer = UserImageSerializer(data=request.data)
        if serializer.is_valid():
            image_base64 = serializer.data.get('image_base64')
            image_path = convert_base64_to_image(image_base64)
            user.profile.profile_image = '%s' % image_path.split('/media/')[1]
            user.profile.save()
            return Response({
                'msg': 'success'
            }, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        user.profile.profile_image = ''
        user.profile.save()
        return Response({
            'msg': 'success'
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTAuthentication,))
def profile_infos(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method in ['POST', 'PUT']:
        serializer = ProfileSerializer(user.profile, data=request.data)
        if serializer.is_valid():
            user_profile = serializer.save()

            return Response(ProfileSerializer(user_profile).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        return Response(ProfileSerializer(user.profile).data, status=status.HTTP_200_OK)
