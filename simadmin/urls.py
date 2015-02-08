from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'siteadmin.views.home', name='home'),
    url(r'^reports$', 'siteadmin.views.reports', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^_/website/sync', 'siteadmin.views.website_sync'),
    url(r'^_/website/add', 'siteadmin.views.website_add'),
    url(r'^_/website/remove', 'siteadmin.views.website_remove'),

    url(r'^admin/', include(admin.site.urls)),
)
