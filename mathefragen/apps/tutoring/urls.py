from django.urls import path

from .views import (
    AskTutors,
    TutoringSessions,
    RequestDetail,
    message_send,
    pay_and_join,
    process_payment,
    payment_success,
    save_tutor_review,

    tutor_settings,
    tutor_videos,
    video_watch_view,
    update_tutoring_status,
    update_tutor_price,
    update_video,
    update_target_group,
    change_payment_type,
    confirm_payment_type,
    delete_payment_type,
    request_payout,
    decline_tutoring_request,
    declined_tutoring_request,
)


urlpatterns = [
    path('ask-tutors/', AskTutors.as_view(), name='ask_tutors'),
    path('ask-tutor/<str:user_hash_id>/', AskTutors.as_view(), name='ask_single_tutor'),
    path('sessions/<str:user_hash_id>/', TutoringSessions.as_view(), name='tutoring_sessions'),

    path('request/detail/<str:request_hash>/', RequestDetail.as_view(), name='request_detail'),

    path('request/detail/<str:request_hash>/send-msg/', message_send, name='message_send'),
    path('request/decline/<str:request_hash>/', decline_tutoring_request, name='decline_tutoring_request'),
    path('request/declined/<str:request_hash>/', declined_tutoring_request, name='declined_tutoring_request'),

    path('pay-and-join/<str:session_id>/', pay_and_join, name='pay_and_join'),
    path('process_payment/<str:session_id>/', process_payment, name='process_payment'),
    path('payment_success/<str:session_id>/', payment_success, name='payment_success'),

    path('review/<str:session_id>/', save_tutor_review, name='save_tutor_review'),

    path('profile/<int:pk>/settings/', tutor_settings, name='tutor_settings'),
    path('profile/<int:pk>/videos/', tutor_videos, name='tutor_videos'),
    path('profile/videos/watch-view/<str:hash_id>/', video_watch_view, name='video_watch_view'),

    path('update-price/<int:pk>/', update_tutor_price, name='update_tutor_price'),
    path('update-status/<int:pk>/', update_tutoring_status, name='update_tutoring_status'),
    path('update-video/<int:pk>/', update_video, name='update_video'),
    path('update-target-group/<int:pk>/', update_target_group, name='update_target_group'),

    path('change-payment-type/<int:pk>/', change_payment_type, name='change_payment_type'),
    path('confirm-payment-type/<int:pk>/', confirm_payment_type, name='confirm_payment_type'),
    path('delete-payment-type/<int:pk>/', delete_payment_type, name='delete_payment_type'),
    path('request-payout/<int:pk>/', request_payout, name='request_payout'),
]
