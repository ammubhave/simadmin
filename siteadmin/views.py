from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
import json
import os

# Create your views here.
def home(request):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
    websites_names = os.listdir(os.path.join(root, 'web_root'))
    websites = []
    for name in websites_names:
        website = {
            'path': '',
            'name': name,
            'has': '',
            'repo': ''
        }
        try:
            with open(os.path.join(os.path.join(os.path.join(root, 'web_root'), name), 'releases/current/meta/config.json')) as f:
                data = json.loads(f.read())
            path = data.get('path', '')
            repo = data.get('repo', '')
            has = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, cwd=os.path.join(os.path.join(os.path.join(root, 'web_root'), name), 'repository')).stdout.read()
            website['path'] = path
            website['has'] = has
            website['repo'] = repo
        except Exception, ex:
            pass
        websites.append(website)

    return render_to_response('home.html', {
            'websites': websites
        })


@csrf_exempt
def website_sync(request):
    return StreamingHttpResponse(website_sync_stream_response_generator(request.POST['id']))


def website_sync_stream_response_generator(app):
    import subprocess
    popen = subprocess.Popen(['../../.venv/bin/fab', 'local_sync:' + app], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read() # yield line
