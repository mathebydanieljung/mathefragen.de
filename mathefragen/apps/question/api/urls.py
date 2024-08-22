from django.urls import path

from mathefragen.apps.question.api.views import (
    # question
    create_question,
    questions_list,
    question_detail,
    question_put,
    question_delete,
    hottest_questions,

    # answer
    answers_list,
    create_answer,
    answer_detail,
    answer_put,
    answer_delete,
    accept_answer,
    all_answers_list,

    # answer comment
    create_answer_comment,
    answer_comments_list,
    answer_comment_put,
    answer_comment_delete,

    # question comments
    question_comments_list,
    create_question_comment,
    question_comment_detail,
    question_comment_put,
    question_comment_delete,

    upload_image
)

urlpatterns = [
    path('', questions_list, name='api_questions_list'),
    path('hot/', hottest_questions, name='hottest_questions'),
    path('answers/', all_answers_list, name='api_all_answers_list'),
    path('create/', create_question, name='api_create_question'),
    path('upload_image/', upload_image, name='api_upload_image'),

    path('<int:question_id>/', question_detail, name='api_question_detail'),
    path('<int:question_id>/change/', question_put, name='api_question_put'),
    path('<int:question_id>/delete/', question_delete, name='api_question_delete'),

    path('<int:question_id>/answer/', answers_list, name='api_question_answers_list'),
    path('<int:question_id>/answer/create/', create_answer, name='api_create_answer'),
    path('<int:question_id>/answer/<int:answer_id>/', answer_detail, name='api_answer_detail'),
    path('<int:question_id>/answer/<int:answer_id>/change/', answer_put, name='api_answer_put'),
    path('<int:question_id>/answer/<int:answer_id>/accept/', accept_answer, name='api_accept_answer'),
    path('<int:question_id>/answer/<int:answer_id>/delete/', answer_delete, name='api_answer_delete'),

    path('answer/<int:answer_id>/comment/create/', create_answer_comment, name='api_create_answer_comment'),
    path('answer/<int:answer_id>/comment/', answer_comments_list, name='api_answer_comments_list'),
    path('answer/<int:answer_id>/comment/<int:comment_id>/change/', answer_comment_put, name='api_answer_comment_put'),
    path('answer/<int:answer_id>/comment/<int:comment_id>/delete/', answer_comment_delete, name='api_answer_comment_delete'),

    path('<int:question_id>/comment/', question_comments_list, name='api_question_comments_list'),
    path('<int:question_id>/comment/create/', create_question_comment, name='api_create_question_comment'),
    path('<int:question_id>/comment/<int:comment_id>/', question_comment_detail, name='api_question_comment_detail'),
    path('<int:question_id>/comment/<int:comment_id>/change/', question_comment_put, name='api_question_comment_put'),
    path('<int:question_id>/comment/<int:comment_id>/delete/', question_comment_delete, name='api_question_comment_delete'),

]
