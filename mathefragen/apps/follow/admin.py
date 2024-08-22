from django.contrib import admin

from mathefragen.apps.follow.models import (
    UserFollow,
    QuestionFollow,
    HashTagFollow
)


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'idate'
    )
    readonly_fields = (
        'follower',
        'following'
    )


@admin.register(QuestionFollow)
class QuestionFollowAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'idate'
    )
    readonly_fields = (
        'follower',
        'question'
    )


@admin.register(HashTagFollow)
class HashTagFollowAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'idate'
    )
    readonly_fields = (
        'follower',
        'hashtag'
    )


