import os
import socket

from django.core.wsgi import get_wsgi_application

if 'macbook' not in socket.gethostname().lower():
    try:
        pass
    except ImportError:
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mathefragen.settings")

application = get_wsgi_application()
