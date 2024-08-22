import json

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt


def page_404(request, exception, template_name=''):
    if 'letsrockmathe' in request.META.get('HTTP_REFERER', ''):
        return redirect('/?bye=letsrockmathe')
    return redirect('/?404=hello-world')


@csrf_exempt
def debug(request):
    request_data = {
        'method': request.method,
        'headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
        'body': request.body.decode('utf-8') if request.body else None,
        'GET': request.GET.dict(),
        'POST': request.POST.dict(),
        'COOKIES': request.COOKIES,
        'FILES': {k: v.name for k, v in request.FILES.items()},
    }

    # Formatierung der Daten als JSON
    response_data = json.dumps(request_data, indent=4)

    return HttpResponse(response_data, content_type='application/json')
