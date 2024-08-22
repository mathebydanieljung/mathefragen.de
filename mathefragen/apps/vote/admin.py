from django.contrib import admin

from .models import Vote, CommentVote


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'answer_comment_id',
        'question_comment_id',
        'idate',
        'user'
    )


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    readonly_fields = (
        'question',
        'answer',
        'type'
    )
    list_display = (
        'idate',
        'type',
        'question_id',
        'answer_id',
        'playlist_id',
        'reason',
        'vote_giver',
        'vote_receiver'
    )
    search_fields = (
        'user__id',
        'question__id',
        'answer__id',
        'playlist__id',
    )

    def vote_giver(self, obj):
        return obj.user.username

    def vote_receiver(self, obj):
        if obj.question_id:
            if obj.question.user_id:
                return obj.question.user.username
            return 'userless question'
        if obj.playlist_id:
            if obj.playlist.user_id:
                return obj.playlist.user.username
            return 'userless playlist'
        return obj.answer.user.username
