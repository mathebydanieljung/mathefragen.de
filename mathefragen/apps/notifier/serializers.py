from rest_framework import serializers


class RefreshSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    fcm_token = serializers.CharField(required=True, max_length=400)


class PushSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField(required=True)
    question_id = serializers.IntegerField(required=True)

