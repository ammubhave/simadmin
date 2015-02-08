from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition

# Create your views here.
def home(request):
    return render_to_response('home.html')  


@csrf_exempt
def website_sync(request):
    return StreamingHttpResponse(website_sync_stream_response_generator(request.POST['id']))


def website_sync_stream_response_generator(app):
    import subprocess, os
    popen = subprocess.Popen(['../../.venv/bin/fab', 'local_sync:' + app], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read() # yield line
