from django.contrib import admin
from django.utils import timezone

from .models import (
    TutorSetting,
    HelpRequest,
    Payment,
    Message,
    PayoutRequest,
    Review
)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'given_by',
        'tutor',
        'public',
        'idate',
        'request'
    )
    readonly_fields = (
        'given_by', 'tutor', 'request', 'text'
    )


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'amount',
        'status',
        'idate',
        'paid_at',
        'paid_by',
        'hash_id'
    )
    readonly_fields = (
        'user',
        'amount',
        'paid_at',
        'paid_by'
    )
    fieldsets = [
        (None, {'fields': (
            'status',
            'user',
            'amount',
            'note'
        )}),
        ('History', {'fields': (
            'paid_at',
            'paid_by'
        )})
    ]

    def save_model(self, request, obj, form, change):
        if not obj.paid_at:
            obj.paid_at = timezone.now()
            obj.save()
        if not obj.paid_by_id:
            obj.paid_by = request.user
            obj.save()

        if 'status' in form.changed_data and obj.status == 'paid':
            obj.inform_tutor_about_payment()

        return super(PayoutRequestAdmin, self).save_model(request, obj, form, change)


@admin.register(TutorSetting)
class TutorSettingAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'is_active',
        'half_hourly_rate',
        'hourly_rate',
        'ninety_min_rate',
        'payment_type',
        'payment_confirmed_at'
    )
    readonly_fields = (
        'user',
        'is_active',
        'half_hourly_rate',
        'hourly_rate',
        'ninety_min_rate',
        'sek_1',
        'sek_2',
        'university_modules',
        'note',
        'payment_type',
        'paypal_email',
        'iban',
        'bic',
        'payment_changed_to',
        'payment_confirm_code',
        'payment_changed_at',
        'payment_change_cancelled_at',
        'payment_confirmed_at'
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    readonly_fields = (
        'sender',
        'request',
        'message'
    )
    list_display = (
        'sender', 'message', 'idate'
    )


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'hash_id',
        'question_user',
        'tutor',
        'question',
        'amount_to_pay',
        'accepted_date_time',
        'paid_at',
        'tutor_joined_at',
        'tutor_completed_at',
        'student_joined_at',
        'student_completed_at',
        'idate'
    )
    readonly_fields = (
        'tutor',
        'user',
        'question',
        'amount_to_pay',
        'users_share',
        'date_time1',
        'date_time2',
        'date_time3',
        'accepted_date_time',
        'accepted_at',
        'duration',
        'last_acted_user',
        'paid_at',
        'started_at',
        'tutor_completed_at',
        'student_completed_at',
        'tutor_joined_at',
        'student_joined_at',
    )
    fieldsets = [
        ('Session', {'fields': (
            'tutor',
            'user',
            'accepted_date_time',
            'amount_to_pay',
            'duration',
            'question'
        )}),
        ('Timestamps', {'fields': (
            'paid_at',
            'started_at',
            'tutor_completed_at',
            'student_completed_at',
            'tutor_joined_at',
            'student_joined_at',
        )}),
    ]

    @staticmethod
    def question_user(obj):
        if obj.question_id:
            if obj.question.user_id:
                return obj.question.user.username
            return 'question without user'

        elif obj.user_id:
            return obj.user.username

        return 'no user'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
    )
    list_display = (
        'hash_id',
        'idate',
        'user',
        'tutor_name',
        'paid_amount',
        'commission',
        'users_share'
    )

    @staticmethod
    def tutor_name(obj):
        if obj.request:
            return obj.request.tutor.username
        return '---'
