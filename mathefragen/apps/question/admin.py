from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from .models import (
    Question,
    Answer,
    QuestionComment,
    AnswerComment,
    AnswerRecommendation
)


class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0
    exclude = (
        'grasp_level',
        'edited_by',
        'edited_at'
    )
    readonly_fields = (
        # 'user',
        'edited_by',
        'source_ip',
        'soft_deleted_at',
        'vote_points',
        'accepted',
        'accepted_at'
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class QuestionCommentInline(admin.StackedInline):
    model = QuestionComment
    extra = 0
    readonly_fields = (
        # 'user',
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    def view_on_site(self, obj):
        return 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())

    actions = ['delete_selected']
    sortable_by = ['title', 'idate']
    inlines = [AnswerInline, QuestionCommentInline]
    search_fields = ('title', 'text', 'hash_id', 'last_acted_user_username')
    list_filter = ('type', 'is_active')
    list_display = (
        'id',
        'title',
        'is_first_question',
        'last_acted_user_username',
        'user_joined_at',
        'number_answers',
        'views',
        'idate',
        'is_active'
    )
    exclude = (
        'followers',
        'points',
        'views',
        'device',
        'anonymous',
        'rank_date',
        'rank_reason',
        'edited_by',
        'last_acted_user',
        'solved_with_tutor',
        'last_acted_user_url',
        'last_acted_user_verified',
        'tag_names'
    )
    readonly_fields = (
        'source_ip',
        'hash_id',
        'answerer',
        'vote_points',
        'number_answers',
        'number_tutor_pings',
        'confirmed',
        'soft_deleted_at',
        'is_first_question',
        'edited_at',
        'source_ip'
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if 'soft_deleted' in form.changed_data and obj.soft_deleted:
            obj.soft_deleted_at = timezone.now()
            obj.save()
        return super(QuestionAdmin, self).save_model(request, obj, form, change)

    @staticmethod
    def user_joined_at(obj):
        if obj.user_id:
            return obj.user.date_joined
        return 'no-user-yet'

    @staticmethod
    def text_start(obj):
        return '%s ...' % obj.text[:100]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    search_fields = ('question_id', 'id', 'text')
    list_filter = ('accepted', 'grasp_level')
    readonly_fields = (
        'question',
        # 'user',
        'source_ip',
        'accepted_at'
    )
    list_display = (
        'id',
        'grasp_level',
        'text_start',
        'accepted',
        'user',
        'question_id',
        'idate',
        'is_active'
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def text_start(self, obj):
        return '%s ...' % obj.text[:50]


@admin.register(QuestionComment)
class QuestionCommentAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    readonly_fields = (
        'question',
        # 'user',
        'source_ip'
    )
    list_display = ('id', 'text_start', 'user', 'question_id', 'idate')

    def text_start(self, obj):
        return '%s ...' % obj.text[:100]


@admin.register(AnswerComment)
class AnswerCommentAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    readonly_fields = (
        'answer',
        # 'user',
        'source_ip'
    )
    list_display = ('id', 'text_start', 'user', 'answer_id', 'idate')

    def text_start(self, obj):
        return '%s ...' % obj.text[:100]


@admin.register(AnswerRecommendation)
class AnswerRecommendationAdmin(admin.ModelAdmin):
    readonly_fields = (
        'answer',
    )
