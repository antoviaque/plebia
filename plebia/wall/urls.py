from django.conf.urls.defaults import *
from wall.models import Post

urlpatterns = patterns('wall.views',
    (r'^$', 'index'),
)

