from django.conf import settings as django_settings

from mathefragen.apps.settings.models import (
    Global,
    HeaderMenu,
    RecommendedBy,
    FooterColumn,
    Performance,
    AppPromotion
)
from mathefragen.apps.stats.models import GlobalStats


def project_settings(request):
    settings = Global.objects.last()
    header_menu = HeaderMenu.objects.last()
    recommended_by = RecommendedBy.objects.last()
    footer_columns = FooterColumn.objects.order_by('id')
    performance = Performance.objects.last()
    mobile_apps = AppPromotion.objects.last()
    stats = GlobalStats.objects.last()
    site_domain = django_settings.DOMAIN
    hot_question_apis = django_settings.HOT_NETWORK_QUESTIONS_API
    is_debug_mode = django_settings.DEBUG
    is_on_mathefragen = 'mathefragen' in request.get_host()
    websockets_enabled = django_settings.ENABLE_WEBSOCKETS

    if not stats:
        stats = GlobalStats.objects.create()

    return {
        'settings': settings,
        'hot_question_apis': hot_question_apis,
        'site_domain': site_domain,
        'header_menu': header_menu,
        'recommended_by': recommended_by,
        'footer_columns': footer_columns,
        'websockets_enabled': websockets_enabled,
        'global_wss_url': django_settings.WEBSOCKET_GLOBAL_PUSH_DOMAIN,
        'user_wss_url': django_settings.WEBSOCKET_USER_PUSH_DOMAIN_BASE,
        'question_wss_url': django_settings.WEBSOCKET_QUESTION_PUSH_DOMAIN_BASE,
        'mobile_apps': mobile_apps,
        'stats': stats,
        'performance': performance,
        'scheme': 'https' if not django_settings.DEBUG else 'http',
        'show_confirm_alert': request.user.is_authenticated and not request.user.is_active,
        'is_debug_mode': is_debug_mode,
        'is_on_mathefragen': is_on_mathefragen,
        'turnstile_site_key': django_settings.TURNSTILE_SITE_KEY,
    }
