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

from django.db import models
from django import forms


# Choices ###########################################################

TORRENT_TYPES = (
    ('season', 'Full season'),
    ('episode', 'Single episode'),
)

TORRENT_STATUSES = (
    ('New', 'New'),
    ('Downloading', 'Downloading'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
)

VIDEO_STATUSES = (
    ('New', 'New'),
    ('Transcoding', 'Transcoding'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
)


# Models ############################################################

class Torrent(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    hash = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, choices=TORRENT_TYPES)
    status = models.CharField(max_length=20, choices=TORRENT_STATUSES, default='New')
    progress = models.FloatField('progress', default=0)
    seeds = models.IntegerField('seeds')
    peers = models.IntegerField('peers')

class Video(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    status = models.CharField(max_length=20, choices=VIDEO_STATUSES, default='New')
    original_path = models.CharField(max_length=200)
    webm_path = models.CharField(max_length=200, blank=True)
    mp4_path = models.CharField(max_length=200, blank=True)
    ogv_path = models.CharField(max_length=200, blank=True)
    image_path = models.CharField(max_length=200, blank=True)

class Series(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    name = models.CharField(max_length=200)

class SeriesSeason(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    series = models.ForeignKey(Series)
    torrent = models.ForeignKey(Torrent, null=True)

class SeriesSeasonEpisode(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    name = models.CharField('name', max_length=200, blank=True)
    season = models.ForeignKey(SeriesSeason)
    torrent = models.ForeignKey(Torrent, null=True, blank=True)
    video = models.ForeignKey(Video, null=True, blank=True)

class Post(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    episode = models.ForeignKey(SeriesSeasonEpisode)


# Forms #############################################################

class PostForm(forms.Form):
    name = forms.CharField(max_length=200)
    season = forms.IntegerField('season')
    episode = forms.IntegerField('episode', required=False)


