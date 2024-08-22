from rest_framework import serializers

from mathefragen.apps.question.models import Question


class SearchQuestionSerializer(serializers.ModelSerializer):
    number_of_answers = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    def get_number_of_answers(self, obj):
        return obj.question_answers.count()

    class Meta:
        model = Question
        fields = (
            'id', 'title', 'text', 'user', 'idate', 'username', 'number_of_answers'
        )


