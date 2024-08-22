from django.urls import path

from .views import video_search

urlpatterns = [
    path('video-search/', video_search, name='video_search'),
]
