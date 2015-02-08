import os
import subprocess
import tempfile
import ldap
import ldap.filter

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.views import login
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator, ValidationError

from django.conf import settings

def zephyr(msg, clas='message', instance='log', rcpt='nobody',):
    proc = subprocess.Popen(
        ['zwrite', '-d', '-n', '-c', clas, '-i', instance, rcpt, ],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    proc.communicate(msg)

def UrlOrAfsValidator(value):
    if value.startswith('/mit/') or value.startswith('/afs/'):
        return
    else:
        try:
            URLValidator()(value)
        except ValidationError:
            raise ValidationError('Provide a valid URL or AFS path')

def pag_check_helper(fn, args, aklog=False, ccname=None, **kwargs):
    if 'executable' in kwargs:
        raise ValueError('"executable" not supported with pag_check_*')

    env = None
    if 'env' in kwargs:
        env = kwargs['env']
        del kwargs['env']
    if ccname:
        if env is not None:
            env = dict(env)
        else:
            env = dict(os.environ)
        env['KRB5CCNAME'] = ccname

    pagsh_cmd = 'exec "$@"'
    if aklog: pagsh_cmd = "aklog && " + pagsh_cmd
    args = ['pagsh', '-c', pagsh_cmd, 'exec', ] + args

    return fn(args, env=env, **kwargs)

def pag_check_call(args, **kwargs):
    return pag_check_helper(subprocess.check_call, args, **kwargs)
def pag_check_output(args, **kwargs):
    return pag_check_helper(subprocess.check_output, args, **kwargs)

def kinit(keytab=None, principal=None, autodelete=True, ):
    if not keytab:
        keytab = settings.KRB_KEYTAB
    if not principal:
        principal = settings.KRB_PRINCIPAL
    assert keytab and principal
    fd = tempfile.NamedTemporaryFile(mode='rb', prefix="krb5cc_djmit_", delete=autodelete, )
    env = dict(KRB5CCNAME=fd.name)
    kinit_cmd = ['kinit', '-k', '-t', keytab, principal, ]
    subprocess.check_call(kinit_cmd, env=env)
    return fd

class ScriptsRemoteUserMiddleware(RemoteUserMiddleware):
    header = 'SSL_CLIENT_S_DN_Email'

class ScriptsRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username, ):
        if '@' in username:
            name, domain = username.split('@')
            assert domain.upper() == 'MIT.EDU'
            return name
        else:
            return username
    def configure_user(self, user, ):
        username = user.username
        user.set_unusable_password()
        con = ldap.open('ldap-too.mit.edu')
        con.simple_bind_s("", "")
        dn = "dc=mit,dc=edu"
        fields = ['cn', 'sn', 'givenName', 'mail', ]
        userfilter = ldap.filter.filter_format('uid=%s', [username])
        result = con.search_s('dc=mit,dc=edu', ldap.SCOPE_SUBTREE, userfilter, fields)
        if len(result) == 1:
            user.first_name = result[0][1]['givenName'][0]
            user.last_name = result[0][1]['sn'][0]
            try:
                user.email = result[0][1]['mail'][0]
            except KeyError:
                user.email = username + '@mit.edu'
            try:
                user.groups.add(auth.models.Group.objects.get(name='mit'))
            except ObjectDoesNotExist:
                print "Failed to retrieve mit group"
        else:
            raise ValueError, ("Could not find user with username '%s' (filter '%s')"%(username, userfilter))
        try:
            user.groups.add(auth.models.Group.objects.get(name='autocreated'))
        except ObjectDoesNotExist:
            print "Failed to retrieve autocreated group"
        user.save()
        return user

def get_or_create_mit_user(username, ):
    """
    Given an MIT username, return a Django user object for them.
    If necessary, create (and save) the Django user for them.
    If the MIT user doesn't exist, raises ValueError.
    """
    user, created = auth.models.User.objects.get_or_create(username=username, )
    if created:
        backend = ScriptsRemoteUserBackend()
        # Raises ValueError if the user doesn't exist
        try:
            return backend.configure_user(user), created
        except ValueError:
            user.delete()
            raise
    else:
        return user, created

def scripts_login(request, **kwargs):
    host = request.META['HTTP_HOST'].split(':')[0]
    if host in ('localhost', '127.0.0.1'):
        return login(request, **kwargs)
    elif request.META['SERVER_PORT'] == '444':
        if request.user.is_authenticated():
            # They're already authenticated --- go ahead and redirect
            if 'redirect_field_name' in kwargs:
                redirect_field_name = kwargs['redirect_field_names']
            else:
                from django.contrib.auth import REDIRECT_FIELD_NAME
                redirect_field_name = REDIRECT_FIELD_NAME
            redirect_to = request.REQUEST.get(redirect_field_name, '')
            if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            return HttpResponseRedirect(redirect_to)
        else:
            return login(request, **kwargs)
    else:
        # Move to port 444
        redirect_to = "https://%s:444%s" % (host, request.META['REQUEST_URI'], )
        return HttpResponseRedirect(redirect_to)
