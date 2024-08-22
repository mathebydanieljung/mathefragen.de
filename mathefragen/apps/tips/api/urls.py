from django.urls import path

from mathefragen.apps.tips.api.views import (
    promotion
)

urlpatterns = [
    path('promotion/', promotion, name='api_promotion'),

]
