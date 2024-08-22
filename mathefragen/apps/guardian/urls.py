from django.urls import path

from .views import report_content

urlpatterns = [
    path('report/content/', report_content, name='report_content'),
]
