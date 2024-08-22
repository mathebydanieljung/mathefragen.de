from django.urls import path

from .views import (
    questions_with_tag,
    search_for_hashtag,
)


urlpatterns = [
    path('questions/', questions_with_tag, name='questions_with_tag'),
    path('search/', search_for_hashtag, name='search_for_hashtag')
]
