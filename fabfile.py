from fabric.api import *
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
