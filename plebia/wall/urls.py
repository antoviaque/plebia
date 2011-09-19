#
# Copyright (C) 2011 Xavier Antoviaque <xavier@antoviaque.org>
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

# Includes ##########################################################

from django.conf.urls.defaults import *
from tastypie.api import Api
from wall.api import *
from wall.models import Post


# API init ##########################################################

v1_api = Api(api_name='v1')
v1_api.register(VideoResource())
v1_api.register(TorrentResource())
v1_api.register(SeriesResource())
v1_api.register(SeasonResource())
v1_api.register(EpisodeResource())
v1_api.register(PostResource())


# URL patterns ######################################################

urlpatterns = patterns('wall.views',
    (r'^$', 'index'),
    (r'^ajax/search/(?P<search_string>.+)$', 'ajax_search'),
    (r'^ajax/newpost/(?P<series_id>\d+)/$', 'ajax_new_post'),
    (r'^ajax/startdownload/(?P<episode_id>\d+)/$', 'ajax_start_download'),
    (r'^api/', include(v1_api.urls)),
)

