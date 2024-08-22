from django.contrib import admin
from django.utils.html import mark_safe
from django.conf import settings

from .models import (
    ReportedAnswer,
    ReportedQuestion,
    ReportedPlaylist,
    BlockedIP
)


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ('ip', 'idate')


@admin.register(ReportedPlaylist)
class ReportedPlaylistAdmin(admin.ModelAdmin):
    list_display = ('id', 'idate', 'reported_by', 'reason')
    search_fields = ('playlist_id',)
    readonly_fields = (
        'reported_by',
        'playlist'
    )


@admin.register(ReportedAnswer)
class ReportedAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'idate', 'reported_by', 'reason')
    search_fields = ('answer_id',)
    readonly_fields = (
        'reported_by',
        'answer'
    )


@admin.register(ReportedQuestion)
class ReportedQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'idate', 'question_link', 'reported_by', 'reason')
    search_fields = ('question_id',)
    readonly_fields = (
        'reported_by',
        'question'
    )

    def question_link(self, obj):
        link = 'https://%s%s' % (
            settings.DOMAIN, obj.question.get_absolute_url()
        )
        return mark_safe(
            '<a href="%s" target="_blank">%s</a>' % (
                link, link
            )
        )
