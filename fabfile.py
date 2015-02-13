from fabric.api import *
import json
import os
import subprocess

# Default release is 'current'
env.release = 'current'


# Environment configuration

def wh():
    """Configuration for waffle-house"""
    env.user = 'root'
    env.hosts = ['waffle-house.mit.edu']
    env.path = '/var/www/simadmin'
    env.branch = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE).stdout.read()

def sd():
    """Configuration for simmons-dev aka waffle-house"""
    wh()


# Actions

def setup():
    """Setup a fresh virtualenv, checks out latest code
    and install everything we need so we are read to deploy"""
    run('mkdir -p %(path)s' % env)
    with cd(env.path):
        # Create the virtualenv
        run('virtualenv .venv')
        run('mkdir releases; mkdir shared;')
        _clone_repo()
        _checkout_latest()
        _install_requirements()


def deploy():
    """Deploys the currently checkout branch"""
    _checkout_latest()
    _install_requirements()
    _symlink_current_release()
    reload()


def _clone_repo():
    with cd(env.path):
        run('git clone https://github.com/ammubhave/simadmin.git repository')

def _checkout_latest():
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    with cd(env.path):
        with cd('repository'):
            run('git fetch')
            run('git checkout %(branch)s' % env)
            run('git submodule update --init')
        run('cp -R repository releases/%(release)s' % env)
        run('rm -rf releases/%(release)s/.git*' % env)


def _install_requirements():
    """Install the requirements packages using pip"""
    with cd(env.path):
        run('.venv/bin/pip install -r releases/%(release)s/requirements.txt' % env)


def _symlink_current_release():
    with cd(env.path):
        with settings(warn_only=True), cd('releases'):
            run('rm previous; mv current previous;' % env)
            run('ln -s %(release)s current' % env)
        with settings(warn_only=True):
            run('rm shared/static')
        run('ln -s ../releases/%(release)s/static shared/static' % env)
        run('cp releases/current/conf/simadmin.conf /etc/httpd/conf.d/simadmin.conf')        


def rollback():
    """Limited rollback. Swaps between the previous and current release"""
    with cd(env.path), cd('releases'):
        run('mv current _previous')
        run('mv previous current')
        run('mv _previous previous')
        run('cp current/conf/simadmin.conf /etc/httpd/conf.d/simadmin.conf')
    reload()


def local_sync(name):
    import time
    env.path = '/var/www/web_root/' + name
    env.release = time.strftime('%Y%m%d%H%M%S')
    with lcd(env.path):
       # print 'execuring local ls'
        with lcd('repository'):
            local('git pull')
            local('git submodule update --init')
        local('cp -R repository releases/%(release)s' % env)
        local('rm -rf releases/%(release)s/.git*' % env)
        with settings(warn_only=True), lcd('releases'):
            local('rm previous; mv current previous;' % env)
            local('ln -s %(release)s current' % env)
        local('touch /var/www/apache_config/_reload_apache_flag')


def local_add_static(repo, name, serve_root):
    # Sanity checks
    if os.path.exists('/var/www/web_root/' + repo):
        print 'ERROR: ' + '/var/www/web_root/' + repo + ' already exists.'
        return
    if os.path.exists('/var/www/apache_config/simadmin/meta' + repo + '.json'):
        print 'ERROR: ' + '/var/www/apache_config/simadmin/meta' + repo + '.json already exists.'
        return

    # All's good, let's deploy!
    with lcd('/var/www/web_root'):
        local('mkdir -p ' + name)
        with lcd(name):
            local('git clone ' + repo + ' repository')
            local('mkdir -p releases')

    
    with open('/var/www/apache_config/simadmin/meta/' + name + '.json', 'w') as f:
        f.write(json.dumps({
            'path': name,
            'repo': repo,
            'type': 'static',
            'serve_root': serve_root,
        }))

    local_sync(name)


def local_remove(name):
    # Remove all website data and configs
    local('rm /var/www/apache_config/simadmin/meta/' + name + '.json')
    local('rm -r /var/www/web_root' + name)

    # Do a apache graceful
    local('touch /var/www/apache_config/_reload_apache_flag')


# Apache commands

def reload():
    """Does graceful reload of apache"""
    run('apachectl configtest')
    run('apachectl -k graceful')


def stop():
    """CAUTION! Stops apache"""
    run('apachectl -k stop')


def start():
    """Starts apache"""
    run('apachectl -k start')


def restart():
    """Restarts apache (not graceful), checks for valid config first"""
    run('apachectl configtest')
    run('apachectl -k restart')
