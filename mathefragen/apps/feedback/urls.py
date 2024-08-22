from django.urls import path

from mathefragen.apps.feedback.views import (
    send_feedback,
    save_channel_suggestion
)

urlpatterns = [
    path('send/', send_feedback, name='send_feedback'),
    path('channel-suggestion/', save_channel_suggestion, name='save_channel_suggestion'),
]
