from django.conf.urls.defaults import *
from tastypie.api import Api
from wall.api import *
from wall.models import Post

# API
v1_api = Api(api_name='v1')
v1_api.register(VideoResource())
v1_api.register(TorrentResource())
v1_api.register(SeriesSeasonEpisodeResource())
v1_api.register(PostResource())

# URLs
urlpatterns = patterns('wall.views',
    (r'^$', 'index'),
    (r'^api/', include(v1_api.urls)),
    (r'^ajax/video/(?P<post_id>\d+)/$', 'video'),
)

