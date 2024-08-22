from django.contrib import admin

from .models import GlobalStats


@admin.register(GlobalStats)
class GlobalStatsAdmin(admin.ModelAdmin):
    list_display = (
        'total_questions',
        'total_users',
        'total_answers',
        'percent_answered',
        'unanswered_questions',
        'answered_questions'
    )
    list_display_links = None
