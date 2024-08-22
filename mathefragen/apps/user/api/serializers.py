from rest_framework import serializers

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from mathefragen.apps.user.models import Profile


class UserSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    def get_profile_image(self, obj):
        if obj.profile.profile_image:
            return '%s' % obj.profile.profile_image.url
        return 'https://media.mathefragen.de/static/images/default_user_imag.png'

    def get_points(self, obj):
        return obj.profile.points

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'date_joined', 'profile_image', 'first_name', 'last_name', 'points'
        )


class UserImageSerializer(serializers.Serializer):
    image_base64 = serializers.CharField()


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
        )


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    token = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password'
        )

    def save(self, **kwargs):
        username = self.validated_data.get('username').lower()
        email = self.validated_data.get('email').lower()

        new_user = User.objects.create(
            username=username,
            email=email,
            is_active=True
        )
        new_user.set_password(raw_password=self.validated_data.get('password'))
        new_user.save()

        return new_user


class LoginSerializer(serializers.Serializer):
    login_id = serializers.CharField(required=True)
    login_pwd = serializers.CharField(required=True)

    def get_user(self):
        login_id = self.validated_data.get('login_id').lower()
        login_pwd = self.validated_data.get('login_pwd')

        try:
            validate_email(login_id)
            valid_email = True
        except ValidationError:
            valid_email = False

        if valid_email:
            user = User.objects.filter(email=login_id).last()
        else:
            user = User.objects.filter(username=login_id).last()

        if not user:
            return

        username = user.username

        if authenticate(username=username, password=login_pwd):
            return user


class PrivacySerializer(serializers.Serializer):
    pass


class ProfileSerializer(serializers.ModelSerializer):
    number_of_questions = serializers.SerializerMethodField()
    number_of_answers = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    date_joined = serializers.DateTimeField(source='user.date_joined', required=False)
    username = serializers.CharField(source='user.username', required=False)
    profile_image = serializers.SerializerMethodField()

    def get_badge(self, obj):
        return obj.get_badges

    def get_profile_image(self, obj):
        if obj.profile_image:
            return '%s' % obj.profile_image.url
        return 'https://media.mathefragen.de/static/images/default_user_imag.png'

    def save(self, **kwargs):
        bio_text = self.validated_data.get('bio_text')
        skills = self.validated_data.get('skills')
        status = self.validated_data.get('status')
        other_status = self.validated_data.get('other_status')
        hide_email = self.validated_data.get('hide_email')
        hide_full_name = self.validated_data.get('hide_full_name')
        hide_username = self.validated_data.get('hide_username')

        # institution = self.validated_data.get('institution') # todo: finalize later
        user_email = self.validated_data.get('user', {}).get('email')
        first_name = self.validated_data.get('user', {}).get('first_name')
        last_name = self.validated_data.get('user', {}).get('last_name')
        username = self.validated_data.get('user', {}).get('username')

        profile = self.instance

        if user_email:
            # todo: inform user about email change
            profile.user.email = user_email

        if bio_text is not None:
            profile.bio_text = bio_text

        if skills is not None:
            profile.skills = skills

        if status is not None:
            profile.status = status

        if other_status is not None:
            profile.other_status = other_status

        if hide_email is not None:
            profile.hide_email = hide_email

        if hide_full_name is not None:
            profile.hide_full_name = hide_full_name

        if hide_username is not None:
            profile.hide_username = hide_username

        if first_name:
            profile.user.first_name = first_name

        if last_name:
            profile.user.last_name = last_name

        if username:
            # todo: check if username already exists
            profile.user.username = username

        profile.user.save()
        profile.save()

        return profile

    def get_number_of_questions(self, obj):
        return obj.user.user_questions.count()

    def get_number_of_answers(self, obj):
        return obj.user.user_answers.count()

    class Meta:
        model = Profile
        fields = (
            'user_id',
            'bio_text',
            'skills',
            'email',
            'number_of_questions',
            'date_joined',
            'number_of_answers',
            'points',
            'username',
            'first_name',
            'last_name',
            'profile_image',
            'status',
            'hide_email',
            'hide_full_name',
            'hide_username'
        )
