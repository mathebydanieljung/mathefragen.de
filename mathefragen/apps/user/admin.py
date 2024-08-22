from django.contrib import admin
from django.utils.html import mark_safe
from django.conf import settings

from .models import (
    Profile,
    Badge
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'power_report', 'can_edit_questions', 'can_edit_answers'
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    def view_on_site(self, obj):
        return 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())

    list_filter = ('found_us_in', 'synced', 'verified')
    filter_horizontal = (
        'badges',
    )
    readonly_fields = (
        'user',
        'points',
        'reached_ppl',
        'total_answers',
        'answers_this_month',
        'answered_month',
        'answers_this_week',
        'answered_week',
        'filled_data_at',
        'skipped_data_at'
    )
    exclude = (
        'social_sign',
        'last_active',
        'bio_text',
        'knowledge_state',
        'skills',
        'fcm_token',
        'phone_number',
        'confirm_hash',
        'pw_onetime_hash',
        'profile_image',
        'wp_id',
        'origin',
        'hide_email',
        'hide_full_name',
        'hide_username',
        'status',
        'other_status',
        'postal_code',
        'found_us_in',
        'institution',
        'filled_data_at',
        'skipped_data_at'
    )
    list_display = (
        'id',
        'user',
        'verified',
        'idate',
        'user_questions',
        'user_answers',
        'current_earnings_as_tutor',
        'total_earnings_as_tutor',
        'payable_amount',
    )
    search_fields = (
        'wp_id',
        'user__username',
        'confirm_hash',
        'hash_id'
    )
    fieldsets = [
        (None, {'fields': (
            'user',
            'badges',
            'verified',
            'reported',
            'soft_deleted',
            'can_tutor',
        )}),
        ('Stats', {'fields': (
            'answers_this_month',
            'answered_month',
            'answers_this_week',
            'answered_week',
            'total_answers'
        )}),
    ]

    def save_model(self, request, obj, form, change):
        if 'verified' in form.changed_data and obj.verified:
            obj.send_verification_email()
            obj.update_question_speed_fields()
        return super(ProfileAdmin, self).save_model(request, obj, form, change)

    def user_questions(self, obj):
        admin_link = '<a href="%squestion/question/?user_id=%s" target="_blank">%s Fragen</a>' % (
            settings.ADMIN_URL, obj.user_id, obj.total_questions
        )
        return mark_safe(admin_link)

    def user_answers(self, obj):
        admin_link = '<a href="%squestion/answer/?user_id=%s" target="_blank">%s Antworten</a>' % (
            settings.ADMIN_URL, obj.user_id, obj.total_answers
        )
        return mark_safe(admin_link)

    def user_full_name(self, obj):
        return obj.user.get_full_name()
