from importlib import import_module

from django.shortcuts import redirect
from django.contrib.auth import logout
from django.conf import settings
from django.contrib.sessions import middleware

from mathefragen.apps.stats.models import GlobalStats


class AccountCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        request.stats = GlobalStats.objects.last()
        request.site_domain = settings.DOMAIN

        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated and not request.user.profile.is_active:
            logout(request)
            return redirect('/user/login/?profile-inactive=1')

        response = self.get_response(request)

        return response


class CORSMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"

        return response
