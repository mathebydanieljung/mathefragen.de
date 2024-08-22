from rest_framework import serializers

from mathefragen.apps.hashtag.models import HashTag


class HashTagSerializer(serializers.ModelSerializer):
    number_of_usages = serializers.SerializerMethodField()

    def get_number_of_usages(self, obj):
        return obj.questions.count()

    class Meta:
        model = HashTag
        fields = (
            'name', 'number_of_usages'
        )
