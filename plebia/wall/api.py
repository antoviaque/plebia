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
# 'AGPLv3'.  If not, see <http://www.gnu.org/licenses/>.
#

# Includes ##########################################################

from tastypie import fields
from tastypie.resources import ModelResource
from wall.models import *


# API resources #####################################################

class VideoResource(ModelResource):
    class Meta:
        queryset = Video.objects.all().order_by('-date_added')
        fields = ['date_added','id','status','image_path','mp4_path','ogv_path','original_path','webm_path']

class TorrentResource(ModelResource):
    class Meta:
        queryset = Torrent.objects.all().order_by('-date_added')
        fields = ['date_added','hash','id','name','peers','progress','seeds','status','type','download_speed','upload_speed','eta']

class SeriesResource(ModelResource):
    season_list = fields.ToManyField('wall.api.SeasonResource', 'season_set')
    class Meta:
        queryset = Series.objects.all().order_by('-date_added')
        fields = ['id','date_added','name', 'tvdb_id', 'overview', 'language', 'rating', 'first_aired', 'airing_status', 'banner_url', 'poster_url', 'fanart_url', 'imdb_id', 'tvcom_id', 'zap2it_id', 'tvdb_last_updated']

class SeasonResource(ModelResource):
    torrent = fields.ForeignKey(TorrentResource, 'torrent', null=True)
    series = fields.ForeignKey(SeriesResource, 'series')
    episode_list = fields.ToManyField('wall.api.EpisodeResource', 'episode_set', full=True)
    class Meta:
        queryset = Season.objects.all().order_by('-date_added')
        fields = ['id','date_added','number','torrent','series']

class EpisodeResource(ModelResource):
    torrent = fields.ForeignKey(TorrentResource, 'torrent', null=True, full=True)
    video   = fields.ForeignKey(VideoResource, 'video', null=True, full=True)
    season  = fields.ForeignKey(SeasonResource, 'season')
    #next_episode = fields.ForeignKey('self', 'next_episode')
    class Meta:
        queryset = Episode.objects.all().order_by('-date_added')
        fields = ['id','date_added','name','number','torrent','season','tvdb_id', 'overview', 'director', 'guest_stars', 'language', 'rating', 'writer', 'first_aired', 'image_url', 'imdb_id', 'tvdb_last_updated','watched']

class PostResource(ModelResource):
    series = fields.ForeignKey(SeriesResource, 'series', full=True)
    class Meta:
        queryset = Post.objects.all().order_by('-date_added')
        fields = ['id','series','date_added']

