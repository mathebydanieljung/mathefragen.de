from django.contrib.auth.models import User
from django.shortcuts import redirect, reverse

from social_core.exceptions import AuthCanceled


def check_email_exists(backend, details, uid, user=None, *args, **kwargs):
    email = details.get('email', '')
    provider = backend.name

    # check if social user exists to allow logging in (not sure if this is necessary)
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    # check if given email is in use
    exists = User.objects.filter(email__iexact=email).exists()

    # user is not logged in, social profile with given uid doesn't exist and email is in use
    if not user and not social and exists:
        return redirect('%s?auth_email_exists=1' % reverse('register'))
