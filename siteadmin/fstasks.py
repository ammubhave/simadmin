import os
import subprocess

from django.conf import settings


def get_website_info(name):
    """Returns a dictionary containing name, path, hash and repo of the given website, or throws
    exception if the given website doesn't exists"""
    website = {}
    with open(os.path.join(settings.EXTERNAL_CONFIG, 'meta/' + name + '.json')) as f:
            data = json.loads(f.read())
            website['path'] = data['path']
            website['repo'] = data['repo']
            website['has'] = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, cwd=os.path.join(settings.WEB_ROOT, name + '/repository')).stdout.read()
    return website


def list_all_websites():
    websites_names = os.listdir(settings.WEB_ROOT)
    websites = []
    for name in websites_names:
        website = get_website_info(name)


def website_add_stream_response_generator(name, repo, type_, details):
    repo_path = os.path.join(settings.WEB_ROOT, name)
    config_path = os.path.join(settings.EXTERNAL_CONFIG, 'meta/' + name + '.json')
    if os.path.exists(repo_path):
        yield 'ERROR: ' + repo_path + ' already exists.'
        return
    if os.path.exists(config_path):
        yield 'ERROR: ' + config_path + ' already exists.'
        return

    if type_ == 'static':
        popen = subprocess.Popen([os.path.join(settings.BASE_DIR, '../../.venv/bin/fab'), 'local_add_static:repo="' + repo + '",name=' + name + ',serve_root=' + details['static_serve_root']], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    else:
        yield 'ERROR: Type ' + type_ + ' is not valid'
        return

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read()
    regenerate_web_root_conf()


def website_remove_stream_response_generator(name):    # Sanity checks
    repo_path = os.path.join(settings.WEB_ROOT, name)
    config_path = os.path.join(settings.EXTERNAL_CONFIG, 'meta/' + name + '.json')
    if not os.path.exists(repo_path):
        yield 'ERROR: ' + repo_path + ' does not exist.'
        return
    if not os.path.exists(config_path):
        yield 'ERROR: ' + config_path + ' does not exist.'
        return

    popen = subprocess.Popen([os.path.join(settings.BASE_DIR, '../../.venv/bin/fab'), 'local_remove:' + name], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read()
    regenerate_web_root_conf()


def website_sync_stream_response_generator(name):
    repo_path = os.path.join(settings.WEB_ROOT, name)
    config_path = os.path.join(settings.EXTERNAL_CONFIG, 'meta/' + name + '.json')
    if not os.path.exists(repo_path):
        yield 'ERROR: ' + repo_path + ' does not exist.'
        return
    if not os.path.exists(config_path):
        yield 'ERROR: ' + config_path + ' does not exist.'
        return

    popen = subprocess.Popen([os.path.join(settings.BASE_DIR, '../../.venv/bin/fab'), 'local_sync:' + name], stdout=subprocess.PIPE, cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        yield line # yield line
    if popen.stderr is not None:
        yield popen.stderr.read()
    regenerate_web_root_conf()


def regenerate_web_root_conf():
    websites_names = os.listdir(settings.WEB_ROOT)
    s = ""
    for name in websites_names:
        try:
            with open(os.path.join(settings.EXTERNAL_CONFIG, 'meta/' + name + '.json')) as f:
                data = json.loads(f.read())
            ev = {
                'path': data['path'],
                'serve_root': data['serve_root'],
                'web_root': settings.WEB_ROOT,
            }
            type_ = data['type']

            if type_ == 'static':
                s += """
Alias /%(path)s "%(web_root)/%(path)s/releases/current/%(serve_root)s"

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
