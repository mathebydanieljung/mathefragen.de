from django.urls import path

from .views import (
    total_numbers,
    deeper_stats
)


urlpatterns = [
    path('numbers/', total_numbers, name='total_numbers'),
    path('numbers/deeper/', deeper_stats, name='deeper_stats'),
]
