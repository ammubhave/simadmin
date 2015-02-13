import os

from django.conf import settings


def get_website_info(name):
    """Returns a dictionary containing name, path, hash and repo of the given website, or throws
    exception if the given website doesn't exists"""
    return {
        'path': name,
        'has': '79605fd0fc34faf7e1b6b271939db77e37d8ba74',
        'repo': 'https://repo@host.com/' + name + '.git',
    }


def list_all_websites():
    websites_names = ['example1', 'example2', 'directory']
    websites = []
    for name in websites_names:
        websites.append(get_website_info(name))
    return websites


def website_add_stream_response_generator(path, repo, type_, details):
    for line in ['Adding website ' + path + ' at ' + repo + ' of type ' + type_ + ' with details ' + str(details) + ' ...', ' Done!']:
        yield line # yield line
    regenerate_web_root_conf()


def website_remove_stream_response_generator(path):
    for line in ['Removing website ' + path + '...', ' Done!']:
        yield line # yield line
    regenerate_web_root_conf()


def website_sync_stream_response_generator(path):
    for line in ['Syncing website ' + path + '...', ' Done!']:
        yield line # yield line
    regenerate_web_root_conf()


def regenerate_web_root_conf():
    print "Regenerating web_root.conf"
    print "=========================="
