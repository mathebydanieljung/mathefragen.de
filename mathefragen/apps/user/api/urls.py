from django.urls import path

from mathefragen.apps.user.api.views import (
    users_list,
    user_detail_get,
    user_detail_delete,
    login_me,
    send_pwd_reset_email,
    register,
    user_image_change,
    profile_infos,
    top_helper
)


urlpatterns = [
    path('login/', login_me, name='api_login_me'),
    path('password/send-magic-link/', send_pwd_reset_email, name='api_send_pwd_reset_email'),
    path('register/', register, name='api_register'),

    path('', users_list, name='api_users_list'),
    path('<int:pk>/', user_detail_get, name='api_user_detail_get'),

    path('<int:pk>/delete/', user_detail_delete, name='api_user_detail_delete'),

    path('profile/<int:pk>/', profile_infos, name='api_profile_infos'),
    path('profile/<int:pk>/image/', user_image_change, name='api_user_image_change'),
    path('profile/<int:pk>/change/', profile_infos, name='api_profile_change'),

    path('top/helper/', top_helper, name='api_top_helper'),
]
