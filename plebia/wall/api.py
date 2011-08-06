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

from tastypie import fields
from tastypie.resources import ModelResource
from wall.models import *


# API resources #####################################################

class VideoResource(ModelResource):
    class Meta:
        queryset = Video.objects.all()
        fields = ["date_added","id","status","image_path","mp4_path","ogv_path","original_path","webm_path"]

class TorrentResource(ModelResource):
    class Meta:
        queryset = Torrent.objects.all()
        fields = ["date_added","hash","id","name","peers","progress","seeds","status","type"]

class SeriesSeasonEpisodeResource(ModelResource):
    torrent = fields.ForeignKey(TorrentResource, 'torrent', null=True)
    video   = fields.ForeignKey(VideoResource, 'video', null=True)
    class Meta:
        queryset = SeriesSeasonEpisode.objects.all()
        fields = ["id","date_added","name","number","torrent"]

class PostResource(ModelResource):
    episode = fields.ForeignKey(SeriesSeasonEpisodeResource, 'episode')
    class Meta:
        queryset = Post.objects.all()
        fields = ['id','episode','date_added']

