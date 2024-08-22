from rest_framework import serializers

from django.conf import settings

from mathefragen.apps.review.models import UserReview


class UserReviewSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    given_by_username = serializers.SerializerMethodField()

    def get_given_by_username(self, obj):
        return obj.given_by.profile.username

    def get_profile_image(self, obj):
        return obj.given_by.profile.get_profile_image()

    class Meta:
        model = UserReview
        fields = (
            'given_by_username', 'text', 'profile_image'
        )

