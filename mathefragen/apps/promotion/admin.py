from django.contrib import admin

from mathefragen.apps.promotion.models import RightPromotion


@admin.register(RightPromotion)
class RightPromotionAdmin(admin.ModelAdmin):
    exclude = ('author',)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'author'):
            obj.author = request.user
        return super(RightPromotionAdmin, self).save_model(request, obj, form, change)
