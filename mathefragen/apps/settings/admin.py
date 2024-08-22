from django.contrib import admin

from .models import (
    Global,
    HeaderMenu,
    MenuChild,
    RecommendedBy,
    FooterColumn,
    FooterRow,
    AppPromotion,
    SEO,
    Snippet,
    Performance
)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    pass


@admin.register(SEO)
class SEOAdmin(admin.ModelAdmin):
    pass


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    pass


@admin.register(AppPromotion)
class AppPromotionAdmin(admin.ModelAdmin):
    pass


@admin.register(Global)
class GlobalAdmin(admin.ModelAdmin):
    pass


@admin.register(HeaderMenu)
class HeaderMenuAdmin(admin.ModelAdmin):
    pass


@admin.register(MenuChild)
class MenuChildAdmin(admin.ModelAdmin):
    pass


@admin.register(RecommendedBy)
class RecommendedByAdmin(admin.ModelAdmin):
    pass


class FooterRowInline(admin.TabularInline):
    model = FooterRow
    extra = 0


@admin.register(FooterColumn)
class FooterColumnAdmin(admin.ModelAdmin):
    inlines = [FooterRowInline]


@admin.register(FooterRow)
class FooterRowAdmin(admin.ModelAdmin):
    pass
