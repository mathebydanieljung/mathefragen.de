from django.urls import path

from mathefragen.apps.vote.api.views import (
    votes, vote_question, vote_answer
)

urlpatterns = [
    path('', votes, name='api_votes_list'),
    path('question/<int:question_id>/', vote_question, name='api_vote_question'),
    path('answer/<int:answer_id>/', vote_answer, name='api_vote_answer'),
]
