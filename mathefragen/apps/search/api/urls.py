from django.urls import path

from mathefragen.apps.search.api.views import (
    search
)


urlpatterns = [
    path('', search, name='api_search'),
]
