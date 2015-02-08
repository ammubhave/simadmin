from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
import json
import os
import subprocess

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

    simadmin_has = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, cwd=os.path.join(root, 'simadmin/repository')).stdout.read()

    user_name = request.META.get('SSL_CLIENT_S_DN_CN', 'Anonymous')
    user_email = request.META.get('SSL_CLIENT_S_DN_Email', 'undefined')

    return render_to_response('home.html', {
            'websites': websites,
            'simadmin_has': simadmin_has,
            'user_name': user_name,
            'user_email': user_email,
        })


@csrf_exempt
def website_add(request):
    return StreamingHttpResponse(website_add_stream_response_generator(request.POST['repo']))


def website_add_stream_response_generator(repo):
    popen = subprocess.Popen(['../../.venv/bin/fab', 'local_add:repo="' + repo + '",app=' + repo[repo.rfind('/') + 1:]], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read() # yield line
    regenerate_web_root_conf()

@csrf_exempt
def website_sync(request):
    return StreamingHttpResponse(website_sync_stream_response_generator(request.POST['id']))


def website_sync_stream_response_generator(app):
    popen = subprocess.Popen(['../../.venv/bin/fab', 'local_sync:' + app], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read() # yield line
    regenerate_web_root_conf()


def regenerate_web_root_conf():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
    websites_names = os.listdir(os.path.join(root, 'web_root'))
    s = ""
    for name in websites_names:
        try:
            with open(os.path.join(os.path.join(os.path.join(root, 'web_root'), name), 'releases/current/meta/config.json')) as f:
                data = json.loads(f.read())
            ev = {
                'repo_name': data['repo'][data['repo'].rfind('/') + 1:],
                'path': data['path'],
                'document_root': data['document_root']
            }
            type_ = data['type']

            if type_ == 'default':
                s += """
Alias /%(path)s "/var/www/web_root/%(repo_name)s/releases/current/%(document_root)s"

<Location /%(path)s>
   Order allow,deny
   Allow from all
   Options +FollowSymLinks
</Location>
""" % ev

        except Exception, ex:
            pass
    with open('/etc/httpd/conf.d/web_root.conf', 'w') as f:
        f.write(s)
