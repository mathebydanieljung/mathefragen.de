import requests
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminMixin, SortableAdminBase
from django.contrib import admin
from django.core.files.storage import default_storage
from django.utils.html import mark_safe

from .models import Playlist, Video, PlaylistCategory


class PlaylistInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Playlist
    extra = 0


@admin.register(PlaylistCategory)
class PlaylistCategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    inlines = [
        PlaylistInline
    ]


class VideoInline(SortableInlineAdminMixin, admin.TabularInline):
    def get_view_on_site_url(self, obj=None):
        return '/admin/video/video/%s/change/' % obj.id

    def has_add_permission(self, request, obj):
        return False

    model = Video
    extra = 0
    verbose_name = 'Video'
    exclude = (
        'description',
        'playlists',
        'tags',
        'youtube_hash'
    )
    verbose_name_plural = 'Video'


@admin.register(Playlist)
class PlaylistAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [
        VideoInline
    ]
    exclude = ('order',)
    list_display = (
        'title', 'videos', 'created_at', 'updated_at'
    )

    @staticmethod
    def videos(obj):
        link = '<a href="/admin/video/video/?playlists=%s">%s Videos</a>' % (obj.id, obj.videos.count())
        return mark_safe(link)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    search_fields = (
        'hash_id', 'youtube_hash'
    )
    list_display = (
        'id',
        'title',
        'owner',
        'file',
        'original_size'
    )
    list_filter = (
        'owner',
    )
    filter_horizontal = (
        'tags',
    )
    fieldsets = [
        ('Video', {
            'fields': (
                'owner',
                'playlist',
                'title',
                'description',
                'file',
                'original_size',
                'tags',
            )
        }),
        ('Thumbnail',
         {
             'fields': (
                 'thumbnail', 'youtube_hash'
             )
         })
    ]

    def save_model(self, request, obj, form, change):
        if 'youtube_hash' in form.changed_data and not obj.thumbnail and obj.youtube_hash:
            url = 'https://i.ytimg.com/vi/%s/hq720.jpg' % obj.youtube_hash

            local_filename = url.split('/')[-1]
            final_path = 'video-thumbnail/%s/%s' % (obj.youtube_hash, local_filename)

            # dont eat up memory if file is too big
            r = requests.get(url, stream=True)
            with default_storage.open(final_path, 'wb+') as destination:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        destination.write(chunk)

            obj.thumbnail = final_path
            obj.save()

        return super(VideoAdmin, self).save_model(request, obj, form, change)
