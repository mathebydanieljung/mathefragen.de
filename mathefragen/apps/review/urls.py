from django.urls import path

from .views import (
    EditReview,
    delete_review,
    CreateReview,
)


urlpatterns = [
    path('profile/<int:pk>/reviews/add/<int:given_to>/', CreateReview.as_view(), name='add_review'),
    path('profile/<int:pk>/reviews/edit/<int:review_id>/', EditReview.as_view(), name='edit_review'),
    path('profile/<int:pk>/reviews/delete/<int:review_id>/', delete_review, name='delete_review'),
]
