from django.urls import path

from .views import (
    follow_user,
    follow_question,
    follow_hashtag,

    unfollow_user,
    unfollow_question,
    unfollow_hashtag
)


urlpatterns = [
    path('user/', follow_user, name='follow_user'),
    path('question/', follow_question, name='follow_question'),
    path('hashtag/', follow_hashtag, name='follow_hashtag'),

    # unfollow
    path('user/user-unfollow/', unfollow_user, name='unfollow_user'),
    path('question/question-unfollow/', unfollow_question, name='unfollow_question'),
    path('hashtag/hashtag-unfollow/', unfollow_hashtag, name='unfollow_hashtag'),
]
