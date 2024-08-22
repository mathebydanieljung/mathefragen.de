from rest_framework import serializers

from django.conf import settings

from mathefragen.apps.question.models import (
    Question,
    Answer,
    QuestionComment,
    AnswerComment
)
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.user.api.serializers import ProfileSerializer
from mathefragen.apps.core.utils import (
    use_mobile_images,
    convert_img_base64_to_html_tag
)


class HotQuestionSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    @staticmethod
    def get_link(obj):
        return 'https://%s%s' % (
            settings.DOMAIN, obj.get_absolute_url()
        )

    class Meta:
        model = Question
        fields = (
            'title',
            'link'
        )


class QuestionSerializer(serializers.ModelSerializer):
    number_of_answers = serializers.SerializerMethodField()
    user = ProfileSerializer(many=False, read_only=True, source='user.profile')
    hashtags = serializers.SerializerMethodField()
    has_voted = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    idate = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()

    def get_views(self, obj):
        return obj.views

    def get_idate(self, obj):
        if obj.rank_date:
            return obj.rank_date.isoformat() + 'Z'
        return obj.idate.isoformat() + 'Z'

    def get_text(self, obj):
        text = use_mobile_images(obj.text)
        text = text.replace(' class="fit_width"', '')
        return text

    def get_has_voted(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            user = request.user
            if user.is_authenticated:
                vote = user.user_votes.filter(question_id=obj.id).last()
                if vote:
                    return vote.type

    def get_username(self, obj):
        return obj.user.username

    def get_hashtags(self, obj):
        return list(obj.question_hashtags.values_list('name', flat=True))

    def get_number_of_answers(self, obj):
        return obj.question_answers.count()

    class Meta:
        model = Question
        fields = (
            'id', 'title', 'text', 'user', 'idate',
            'answered', 'number_of_answers', 'hashtags', 'views', 'votes',
            'has_voted', 'anonymous'
        )


class ImageSerializer(serializers.Serializer):
    media_file = serializers.FileField()


class CreateQuestionSerializer(serializers.ModelSerializer):
    hashtags = serializers.ListField(max_length=100)

    def create(self, validated_data):

        question_text = validated_data.get('text')
        anonymous = validated_data.get('anonymous')

        new_question = Question.objects.create(
            title=validated_data.get('title'),
            text=question_text,
            anonymous=anonymous,
            user_id=validated_data.get('user').id
        )
        hashtags = validated_data.get('hashtags')
        for htag in hashtags:
            htag = htag.lower()
            hashtag = HashTag.objects.filter(name=htag).last()
            if not hashtag:
                hashtag = HashTag.objects.create(name=htag)

            hashtag.questions.add(new_question)

        return new_question

    class Meta:
        model = Question
        fields = (
            'title', 'text', 'user', 'idate', 'hashtags', 'anonymous'
        )


class AnswerSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(many=False, read_only=True, source='user.profile')
    has_voted = serializers.SerializerMethodField()
    question = QuestionSerializer(many=False, read_only=True)
    number_of_comments = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    idate = serializers.SerializerMethodField()

    def get_idate(self, obj):
        return obj.idate.isoformat() + 'Z'

    def get_text(self, obj):
        text = use_mobile_images(obj.text)
        return text

    def get_has_voted(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            user = request.user
            if user.is_authenticated:
                vote = user.user_votes.filter(answer_id=obj.id).last()
                if vote:
                    return vote.type

    def get_number_of_comments(self, obj):
        return obj.answer_comments.count()

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = Answer
        fields = (
            'id', 'text', 'accepted', 'votes', 'question', 'user', 'idate', 'has_voted', 'number_of_comments'
        )


class CreateAnswerSerializer(serializers.ModelSerializer):

    def save(self, **kwargs):
        answer_text = self.validated_data.get('text')
        user_id = self.validated_data.get('user').id

        answer_text = convert_img_base64_to_html_tag(answer_text)
        return Answer.objects.create(
            user_id=user_id, text=answer_text
        )

    class Meta:
        model = Answer
        fields = (
            'text', 'user'
        )


class AnswerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = (
            'text', 'user'
        )


class QuestionCommentSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(many=False, read_only=True, source='user.profile')
    text = serializers.SerializerMethodField()
    idate = serializers.SerializerMethodField()

    def get_idate(self, obj):
        return obj.idate.isoformat() + 'Z'

    def get_text(self, obj):
        text = use_mobile_images(obj.text)
        return text

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = QuestionComment
        fields = (
            'id', 'question', 'user', 'text', 'idate'
        )


class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionComment
        fields = (
            'user', 'text'
        )


class AnswerCommentSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(many=False, read_only=True, source='user.profile')
    text = serializers.SerializerMethodField()
    idate = serializers.SerializerMethodField()

    def get_idate(self, obj):
        return obj.idate.isoformat() + 'Z'

    def get_text(self, obj):
        text = use_mobile_images(obj.text)
        return text

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = AnswerComment
        fields = (
            'id', 'answer', 'user', 'text', 'idate'
        )


class CreateAnswerCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerComment
        fields = (
            'user', 'text'
        )
