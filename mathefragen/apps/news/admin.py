from django.conf import settings
from django.contrib import admin
from django.utils.html import mark_safe

from mathefragen.apps.news.models import News, ReleaseNote


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):

    def view_on_site(self, obj):
        return 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())

    exclude = ('author',)
    list_display = ('id', 'title', 'link')
    summernote_fields = 'text'

    def link(self, obj):
        the_link = 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())
        news_link = '<a href="%s" target="_blank">%s</a>' % (the_link, the_link)
        return mark_safe(news_link)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'author'):
            obj.author = request.user
        return super(NewsAdmin, self).save_model(request, obj, form, change)


@admin.register(ReleaseNote)
class ReleaseNoteAdmin(admin.ModelAdmin):

    def view_on_site(self, obj):
        return 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())

    exclude = ('author',)
    list_display = ('id', 'title', 'link', 'version', 'public', 'public_date')
    summernote_fields = 'text'

    def link(self, obj):
        the_link = 'https://%s%s' % (settings.DOMAIN, obj.get_absolute_url())
        news_link = '<a href="%s" target="_blank">%s</a>' % (the_link, the_link)
        return mark_safe(news_link)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'author'):
            obj.author = request.user
        return super(ReleaseNoteAdmin, self).save_model(request, obj, form, change)
