from django.urls import path

from mathefragen.apps.vote.views import (
    vote_question,
    undo_vote_question,
    vote_answer,
    undo_vote_answer,
    vote_playlist,
    undo_vote_playlist,
    vote_comment,
    undo_vote_comment,
)

urlpatterns = [
    path('question/<int:question_id>/', vote_question, name='vote_question'),
    path('question/<int:question_id>/undo/', undo_vote_question, name='undo_vote_question'),

    path('answer/<int:answer_id>/', vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/undo/', undo_vote_answer, name='undo_vote_answer'),

    path('vote/comment/', vote_comment, name='vote_comment'),
    path('vote/comment/undo/', undo_vote_comment, name='undo_vote_comment'),

    path('playlist/<str:playlist_hash>/', vote_playlist, name='vote_playlist'),
    path('playlist/<str:playlist_hash>/undo/', undo_vote_playlist, name='undo_vote_playlist'),
]
