from functools import wraps

from django.shortcuts import HttpResponse


def refuse_bots(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if 'google' in request.META.get('HTTP_USER_AGENT', ''):
            return HttpResponse('you are bot')

        return function(request, *args, **kwargs)

    return wrap
