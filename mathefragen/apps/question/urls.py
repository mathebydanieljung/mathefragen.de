from django.urls import path

from .views import (
    question_detail,
    reload_tags,
    update_questions_tags,
    question_detail_hashed,
    CreateQuestion,
    delete_question,
    answer_question,
    accept_answer,
    mark_as_solved_with_tutor,
    delete_answer,
    save_question_comment,
    delete_question_comment,
    save_answer_comment,
    delete_answer_comment,
    upload_image,
    convert
)


urlpatterns = [
    path('create/', CreateQuestion.as_view(), name='create_question'),
    path('upload_image/', upload_image, name='upload_image'),

    path('<int:question_id>/<str:slug>/', question_detail, name='question_detail'),
    path('<int:question_id>/<str:slug>/t/reload-tags/', reload_tags, name='reload_tags'),
    path('<int:question_id>/<str:slug>/t/update-tags/', update_questions_tags, name='update_questions_tags'),
    path('q/<str:hash_id>/<str:slug>/', question_detail_hashed, name='question_detail_hashed'),

    path('edit/<int:question_id>/q/', CreateQuestion.as_view(), name='edit_question'),
    path('delete/<int:question_id>/d/', delete_question, name='delete_question'),
    path('answer/<int:question_id>/s/', answer_question, name='answer_question'),
    path('answer/accept/a/', accept_answer, name='accept_answer'),
    path('mark/accept/solved_with_tutor/', mark_as_solved_with_tutor, name='mark_as_solved_with_tutor'),
    path('answer/delete/d/', delete_answer, name='delete_answer'),

    path('convert/', convert, name='convert'),

    path('comment/save/q/', save_question_comment, name='save_question_comment'),
    path('comment/delete/d/', delete_question_comment, name='delete_question_comment'),
    path('answer/comment/save/s/', save_answer_comment, name='save_answer_comment'),
    path('answer/comment/delete/d/', delete_answer_comment, name='delete_answer_comment')
]
