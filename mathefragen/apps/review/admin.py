from django.contrib import admin

from .models import UserReview


@admin.register(UserReview)
class UserReviewAdmin(admin.ModelAdmin):
    search_fields = (
        'given_to__username',
    )
    readonly_fields = (
        'given_by',
        'given_to',
        'source_question',
        'hashtags'
    )
    list_display = (
        'id',
        'idate',
        'given_by',
        'given_to',
        'text',
        'confirmed_hashtags',
        'source_question_id',
        'relation_source'
    )

    def confirmed_hashtags(self, obj):
        return list(obj.hashtags.values_list('name', flat=True))
    confirmed_hashtags.short_description = 'Bestätigte Kenntnisse'
