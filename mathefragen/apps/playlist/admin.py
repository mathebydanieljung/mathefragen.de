from django.contrib import admin

from .models import Playlist, Unit


class AdminUnit(admin.TabularInline):
    model = Unit
    extra = 0


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
        'tags'
    )
    inlines = [AdminUnit]
    list_display = (
        'id',
        'hash_id',
        'name',
        'user',
        'number_units',
        'is_active',
        'vote_points',
        'views'
    )

    @staticmethod
    def number_units(obj):
        return obj.playlist_units.count()


