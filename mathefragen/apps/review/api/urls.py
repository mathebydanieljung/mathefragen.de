from django.urls import path

from mathefragen.apps.review.api.views import (
    top_reviews
)


urlpatterns = [
    path('top/', top_reviews, name='api_top_reviews'),
]
