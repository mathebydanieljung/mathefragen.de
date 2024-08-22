from django.urls import path

from .views import (
    all_playlists,
    profile_playlists,
    AddPlaylist,
    AddPlaylistUnit,
    playlist_detail,
    delete_playlist,
    delete_unit
)


urlpatterns = [
    path('', all_playlists, name='all_playlists'),
    path('u/<str:user_hash>/', profile_playlists, name='profile_playlists'),
    path('<str:slug>/<str:pl_hash>/d/', playlist_detail, name='playlist_detail'),
    path('u/<str:user_hash>/add/', AddPlaylist.as_view(), name='add_playlist'),
    path('<str:pl_hash>/edit/', AddPlaylist.as_view(), name='edit_playlist'),
    path('<str:pl_hash>/add-unit/', AddPlaylistUnit.as_view(), name='add_playlist_unit'),
    path('<str:pl_hash>/delete/', delete_playlist, name='delete_playlist'),
    path('delete_playlist_unit/', delete_unit, name='delete_unit'),
]
