# from django.urls import path
#
# from videos.apps.video.views import (
#     video_detail,
#     video_detail_iframe,
#     stream_video,
#     category_detail,
#     playlist_detail,
#     playlist_detail_iframe
# )
#
# urlpatterns = [
#     path('category/<str:slug>/<str:category_hash>/', category_detail, name='category_detail'),
#
#     path('playlist/<str:slug>/<str:playlist_hash>/', playlist_detail, name='playlist_detail'),
#     path('playlist/<str:slug>/<str:playlist_hash>/iframe/', playlist_detail_iframe, name='playlist_detail_iframe'),
#
#     path('detail/<str:slug>/<str:video_hash>/', video_detail, name='video_detail'),
#     path('detail/<str:slug>/<str:video_hash>/iframe/', video_detail_iframe, name='video_detail_iframe'),
#
#     path('detail/<str:slug>/<str:video_hash>/stream/', stream_video, name='stream_video'),
# ]
