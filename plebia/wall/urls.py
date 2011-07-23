from django.conf.urls.defaults import *
from wall.models import Post

urlpatterns = patterns('wall.views',
    (r'^$', 'index'),
    (r'^ajax/post_detail/(?P<post_id>\d+)/$', 'post_detail'),
    (r'^ajax/video/(?P<post_id>\d+)/$', 'video'),
)

