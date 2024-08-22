from django.contrib import admin
from django.contrib import messages
from django.conf import settings
from django.utils.html import mark_safe

from .models import HashTag


@admin.register(HashTag)
class HashTagAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'number_of_usages', 'question_ids', 'playlist_ids', 'review_ids', 'is_main_tag', 'show_subtags'
    )
    ordering = ('-idate',)
    filter_horizontal = (
        'subtags',
        'questions'
    )
    search_fields = (
        'name',
    )

    @staticmethod
    def show_subtags(obj):
        links = ''
        for h in obj.subtags.all():
            links += '<a href="%shashtag/hashtag/%s/change/">%s</a>, ' % (
                settings.ADMIN_URL, h.id, h.name
            )
        return mark_safe(links)

    @staticmethod
    def question_ids(obj):
        return list(obj.questions.values_list('id', flat=True))

    @staticmethod
    def playlist_ids(obj):
        return list(obj.playlist_set.values_list('id', flat=True))

    @staticmethod
    def review_ids(obj):
        return list(obj.user_review_hashtags.values_list('id', flat=True))

    # we override this, because: if one hashtag gets deleted, we want to make sure, it will be mapped to other existing
    # one so that the question relation stays untouched
    def delete_queryset(self, request, queryset):
        for tag in queryset:
            # if tag is dangling tag, then delete
            if not tag.questions.count() and not tag.playlist_set.count() and not tag.confirmed_hashtags.count():
                tag.delete()
                continue

            # check if same tag exists also
            if HashTag.objects.filter(name__iexact=tag.name).exclude(id=tag.id).count():
                other_tag = HashTag.objects.filter(name__iexact=tag.name).exclude(id=tag.id).last()

                # copy question relations
                for q in tag.questions.all():
                    other_tag.questions.add(q.id)

                # copy playlist relations
                for pl in tag.playlist_set.all():
                    other_tag.playlist_set.add(pl.id)

                for rv in tag.user_review_hashtags.all():
                    other_tag.user_review_hashtags.add(rv.id)

                # now we can delete selected tag
                messages.add_message(request, messages.INFO, 'Hashtag-Relation wurde geshifted und Tag wurde gelöscht')
                tag.delete()

            # if no other same tags, then delete selected tag easily.
            else:
                messages.add_message(request, messages.ERROR, 'ACHTUNG: Bitte nur umbennen! Hashtag wird gerade verwendet')

