import json
import os
import subprocess

from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition

# Create your views here.
def home(request):
    websites = settings.FSTASKS.list_all_websites()
    print websites

    user_name = request.META.get('SSL_CLIENT_S_DN_CN', 'Anonymous')
    user_email = request.META.get('SSL_CLIENT_S_DN_Email', 'undefined')
    is_reload_scheduled = os.path.exists('/var/www/apache_config/_reload_apache_flag')

    return render_to_response('home.html', {
            'websites': websites,
            'user_name': user_name,
            'user_email': user_email,
            'is_reload_scheduled': is_reload_scheduled,
        })


def reports(request):
    user_name = request.META.get('SSL_CLIENT_S_DN_CN', 'Anonymous')
    user_email = request.META.get('SSL_CLIENT_S_DN_Email', 'undefined')

    error_log = subprocess.Popen(['tail', '/var/log/httpd/error_log'], stdout=subprocess.PIPE).stdout.read()
    access_log = subprocess.Popen(['tail', '/var/log/httpd/access_log'], stdout=subprocess.PIPE).stdout.read()

    return render_to_response('reports.html', {
            'error_log': error_log,
            'access_log': access_log,
            'user_name': user_name,
            'user_email': user_email,
        })


@csrf_exempt
def website_remove(request):
    return StreamingHttpResponse(settings.FSTASKS.website_remove_stream_response_generator(request.POST['path']))


@csrf_exempt
def website_add(request):
    details = {}
    if request.POST['type'] == 'static':
        details['static_serve_root'] = request.POST['static-serve-root']
    return StreamingHttpResponse(settings.FSTASKS.website_add_stream_response_generator(request.POST['path'], request.POST['repo'], request.POST['type'], details))


@csrf_exempt
def website_sync(request):
    return StreamingHttpResponse(settings.FSTASKS.website_sync_stream_response_generator(request.POST['path']))
