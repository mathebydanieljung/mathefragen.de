from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from mathefragen.apps.question.models import Question
from mathefragen.apps.question.views import index, CreateQuestion, mathefragen_landing
from mathefragen.apps.tips.api.views import promotion

questions_sitemaps_dict = {
    'queryset': Question.objects.order_by('-id'),
    'date_field': 'idate'
}

admin_site = admin.sites.AdminSite
admin_site.site_header = '%s Administration' % settings.DOMAIN

urlpatterns = [
    # API for mobile apps
    path('v1/user/', include('mathefragen.apps.user.api.urls')),
    path('v1/question/', include('mathefragen.apps.question.api.urls')),
    path('v1/vote/', include('mathefragen.apps.vote.api.urls')),
    path('v1/search/', include('mathefragen.apps.search.api.urls')),
    path('v1/hashtag/', include('mathefragen.apps.hashtag.api.urls')),
    path('v1/review/', include('mathefragen.apps.review.api.urls')),

    path('v1/stats/', include('mathefragen.apps.stats.urls')),
    path('v1/banner-promotion/', promotion),

    path('v1/fcm/', include('mathefragen.apps.notifier.urls')),
    path('v1/api-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/api-token-verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('v1/aiedn/', include('mathefragen.apps.aiedn.urls')),

    path('api-auth/', include('rest_framework.urls')),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Webapp urls
    path('', index, name='index'),
    path('landing/', mathefragen_landing, name='mathefragen_landing'),
    path('question/', include('mathefragen.apps.question.urls')),
    path('frage/', include('mathefragen.apps.question.urls')),
    path('nachhilfe/', include('mathefragen.apps.tutoring.urls')),

    # from online scripts
    path('frage-stellen/', CreateQuestion.as_view(), name="ask_question_from_outside"),

    path('tag/', include('mathefragen.apps.hashtag.urls')),
    path('playlists/', include('mathefragen.apps.playlist.urls')),
    path('follow/', include('mathefragen.apps.follow.urls')),
    path('guardian/', include('mathefragen.apps.guardian.urls')),
    path('vote/', include('mathefragen.apps.vote.urls')),
    path('artikel/', include('mathefragen.apps.news.urls')),
    path('user/', include('mathefragen.apps.user.urls')),
    path('review/', include('mathefragen.apps.review.urls')),
    path('search/', include('mathefragen.apps.search.urls')),
    path('feedback/', include('mathefragen.apps.feedback.urls')),

    path('info/apps/', TemplateView.as_view(template_name='apps.html'), name='apps'),
    path('impressum/', TemplateView.as_view(template_name='legal/imprint.html'), name='imprint'),
    path('privacy/', TemplateView.as_view(template_name='legal/privacy.html'), name='privacy'),
    path('terms_of_use/', TemplateView.as_view(template_name='legal/terms.html'), name='terms'),
    path('info/about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('info/videos/', TemplateView.as_view(template_name='videos.html'), name='videos'),
    path('%s' % settings.ADMIN_URL.lstrip('/'), admin.site.urls, name='admin'),

    # sitemap
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': {'questions': GenericSitemap(questions_sitemaps_dict, priority=0.6, protocol='https')}},
        name='django.contrib.sitemaps.views.sitemap'
    ),
    # robots
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type="text/plain")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'mathefragen.apps.core.views.page_404'
