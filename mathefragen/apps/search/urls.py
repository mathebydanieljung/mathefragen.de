from django.urls import path

from .views import (
    search,
    playlist_search,
    youtube_search
)


urlpatterns = [
    path('', search, name='search'),
    path('playlists/', playlist_search, name='playlist_search'),
    path('youtube_search/', youtube_search, name='youtube_search')
]
