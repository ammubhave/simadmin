"""
WSGI config for simadmin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simadmin.settings")

from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

def application(environ, start_response):
    if 'EXTERNAL_CONFIG' in environ:
        os.environ.setdefault('EXTERNAL_CONFIG', environ['EXTERNAL_CONFIG'])
    return _application(environ, start_response)
