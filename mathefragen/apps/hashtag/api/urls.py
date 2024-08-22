from django.urls import path

from mathefragen.apps.hashtag.api.views import (
    hashtag_search
)


urlpatterns = [
    path('<str:hash_tag>/', hashtag_search, name='api_hashtag_search'),
]
