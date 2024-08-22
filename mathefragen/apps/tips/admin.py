from django.contrib import admin

from mathefragen.apps.tips.models import QuestionTip, HelpTip, PromotionBanner


@admin.register(QuestionTip)
class QuestionTipAdmin(admin.ModelAdmin):
    list_display = ('text', 'idate', 'author')

    fieldsets = [
        (None, {'fields': (
            'text',
        )})
    ]

    def save_model(self, request, obj, form, change):
        obj.author = request.user
        return super(QuestionTipAdmin, self).save_model(request, obj, form, change)


@admin.register(HelpTip)
class HelpTipAdmin(admin.ModelAdmin):
    list_display = ('text', 'idate', 'author')

    fieldsets = [
        (None, {'fields': (
            'text',
        )})
    ]

    def save_model(self, request, obj, form, change):
        obj.author = request.user
        return super(HelpTipAdmin, self).save_model(request, obj, form, change)


@admin.register(PromotionBanner)
class PromotionBannerAdmin(admin.ModelAdmin):
    pass


