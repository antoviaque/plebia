from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    (r'^downloads/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.DOWNLOAD_DIR}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DIR}),
    (r'^', include('wall.urls')),
)


