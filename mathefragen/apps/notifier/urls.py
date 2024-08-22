from django.urls import path

from .views import refresh, push


urlpatterns = [
    path('refresh/', refresh, name='refresh'),
    path('push/', push, name='push')
]
