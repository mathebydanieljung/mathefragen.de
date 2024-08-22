from django.urls import path

from .views import detail_news, details_release_note, latest_release_note


urlpatterns = [
    path('<str:hash_id>/<str:slug>/', detail_news, name='detail_news'),
    path('release-notes/', latest_release_note, name='latest_release_note'),
    path('release/<str:hash_id>/<str:slug>/', details_release_note, name='details_release_note')
]
