from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    Login,
    ConfirmMissingView,
    Register,
    JoinWithQuestion,
    sync_new_user,
    PasswordForgotView,
    SetPasswordView,
    all_users,
    public_profile,
    public_profile_hashed,
    update_basic_info,
    fill_missing_data,
    skip_profile_completion,
    change_pwd,
    resend_confirm_email,
    register_confirm,
    change_image,
    change_privacy,
    delete_account,
    profile_socials,
    ProfileReviews,
    AddSocials,
    delete_social,
    EditSocials,
    profile_settings,
    public_profile_answers,
    public_profile_following_content,
    public_profile_articles,
    inbox,
    fetch_messages,
    update_last_active,
    ApplyVerificationView,
    download_certificate,
    set_profile_image
)
from ..core.views import debug

urlpatterns = [
    path('all/', all_users, name='all_users'),

    # delete this later
    path('profile/<int:pk>/', public_profile, name='public_profile'),

    path('p/<str:hash_id>/', public_profile_hashed, name='public_profile_hashed'),
    path('p/<str:hash_id>/set-image/', set_profile_image, name='set_profile_image'),

    path('profile/<int:pk>/download-certificate/', download_certificate, name='download_certificate'),

    path('profile/<int:pk>/active/', update_last_active, name='update_last_active'),

    path('profile/<int:pk>/inbox/', inbox, name='inbox'),
    path('profile/<int:pk>/inbox/fetch_messages/', fetch_messages, name='fetch_messages'),

    path('profile/<int:pk>/answers/', public_profile_answers, name='public_profile_answers'),
    path('profile/<int:pk>/articles/', public_profile_articles, name='public_profile_articles'),
    path('profile/<int:pk>/following/', public_profile_following_content, name='public_profile_following_content'),

    path('profile/<int:pk>/socials/', profile_socials, name='profile_socials'),
    path('profile/<int:pk>/socials/add/', AddSocials.as_view(), name='add_socials'),
    path('profile/<int:pk>/socials/<int:social_pk>/edit/', EditSocials.as_view(), name='edit_socials'),
    path('profile/<int:pk>/socials/<int:social_pk>/delete/', delete_social, name='delete_social'),

    path('profile/<int:pk>/reviews/', ProfileReviews.as_view(), name='profile_reviews'),
    path('profile/<int:pk>/settings/', profile_settings, name='profile_settings'),
    path('profile/<int:pk>/settings/resend_confirm_email/', resend_confirm_email, name='resend_confirm_email'),

    path('profile/<int:pk>/update_basic_info/', update_basic_info, name='update_basic_info'),
    path('profile/<int:pk>/fill_missing_data/', fill_missing_data, name='fill_missing_data'),
    path('profile/<int:pk>/skip_profile_completion/', skip_profile_completion, name='skip_profile_completion'),
    path('profile/<int:pk>/change_pwd/', change_pwd, name='change_pwd'),
    path('profile/<int:pk>/change_image/', change_image, name='change_image'),
    path('profile/<int:pk>/change_privacy/', change_privacy, name='change_privacy'),
    path('verification/apply/', ApplyVerificationView.as_view(), name='apply_verification'),

    path('login/', Login.as_view(), name='login'),
    path('confirm/pending/', ConfirmMissingView.as_view(), name='confirm_pending'),
    path('forgot_password/', PasswordForgotView.as_view(), name='password_forgot'),
    path('set_password/<str:pw_onetime_hash>/', SetPasswordView.as_view(), name='set_password'),
    path('join-with-question/', JoinWithQuestion.as_view(), name='join_with_question'),
    path('register/', Register.as_view(), name='register'),
    path('sync/', sync_new_user, name='sync_new_user'),

    path('register/confirm/<str:confirm_hash>/', register_confirm, name='register_confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('delete/', delete_account, name='delete_my_account'),

    path('debug/', debug, name='debug'),
]
