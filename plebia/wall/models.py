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

from django.db.models.signals import pre_save, post_save
from django.db import models
from django import forms

from lxml.html import soupparser
from lxml.cssselect import CSSSelector

import re
import mechanize

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
    download_speed = models.CharField(max_length=20, blank=True)
    upload_speed = models.CharField(max_length=20, blank=True)
    eta = models.CharField(max_length=20, blank=True)

    def __unicode__(self):
        return ("%s %s %s" % (self.name, self.hash, self.type))


class Video(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    status = models.CharField(max_length=20, choices=VIDEO_STATUSES, default='New')
    original_path = models.CharField(max_length=200)
    webm_path = models.CharField(max_length=200, blank=True)
    mp4_path = models.CharField(max_length=200, blank=True)
    ogv_path = models.CharField(max_length=200, blank=True)
    image_path = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return ("%s %s" % (self.original_path, self.status))


class Series(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=200)

    def __unicode__(self):
        return ("%s" % (self.name))

    def update_seasons(self):
        # Get list of series & episode from URL and create/update objects as necessary
        url = 'http://www.kat.ph' + self.url
        print url
        episode_dom_list = get_dom_selection_from_url('.mainpart table td .infoListCut', url)
        next_episode = None
        for episode_dom in episode_dom_list:
            season_nb = int(episode_dom.getparent().getparent().getprevious().text_content()[7:])
            episode_nb = int(episode_dom.cssselect('.versionsEpNo')[0].text_content()[8:])
            
            season = SeriesSeason.objects.get_or_create(series=self, number=season_nb)[0]
            episode = SeriesSeasonEpisode.objects.get_or_create(season=season, number=episode_nb)[0]

            episode.next_episode = next_episode
            episode.save()
            next_episode = episode


class SeriesSeason(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    series = models.ForeignKey(Series)
    torrent = models.ForeignKey(Torrent, null=True)
    
    def __unicode__(self):
        return ("%s (season %s)" % (self.series, self.number))


class SeriesSeasonEpisode(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    name = models.CharField('name', max_length=200, blank=True)
    season = models.ForeignKey(SeriesSeason)
    torrent = models.ForeignKey(Torrent, null=True, blank=True)
    video = models.ForeignKey(Video, null=True, blank=True)
    next_episode = models.ForeignKey('self', null=True, blank=True)
    
    def __unicode__(self):
        return ("%s (number %d)" % (self.season, self.number))

    def start_download(self):
        from plebia.wall import torrentutils

        if self.torrent is None:
            torrent = torrentutils.get_torrent_by_episode(self)
            self.torrent = torrent
            self.save()


class Post(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    episode = models.ForeignKey(SeriesSeasonEpisode, null=True, blank=True)
    
    def __unicode__(self):
        return ("%s" % (self.episode))


# Forms #############################################################

class PostForm(forms.Form):
    name = forms.CharField(max_length=200)


# Signals & data consistency ########################################

def episode_pre_save(sender, **kwargs):
    episode = kwargs['instance']
    torrent = episode.torrent


def episode_post_save(sender, **kwargs):
    from plebia.wall import torrentutils
    from plebia.wall import videoutils
    created = kwargs['created']
    episode = kwargs['instance']

    # Also immediately try to get the video object for new episodes
    if created and episode.video is None \
            and episode.torrent and episode.torrent.status == 'Completed':
        episode.video = videoutils.locate_video(episode)
        episode.save()


def torrent_pre_save(sender, **kwargs):
    from plebia.wall import videoutils
    torrent = kwargs['instance']

    # Make sure that videos are located for each episode related to a completed torrent
    if torrent.status == 'Completed':
        # There can be several episodes per torrent
        episode_list = torrent.seriesseasonepisode_set.all()
        for episode in episode_list:
            if episode.video is None:
                episode.video = videoutils.locate_video(episode)
                episode.save()


def torrent_post_save(sender, **kwargs):
    episode = kwargs['instance']
    created = kwargs['created']


# Register signal handlers
pre_save.connect(episode_pre_save, sender=SeriesSeasonEpisode, dispatch_uid="episode_pre_save")
post_save.connect(episode_post_save, sender=SeriesSeasonEpisode, dispatch_uid="episode_post_save")
pre_save.connect(torrent_pre_save, sender=Torrent, dispatch_uid="torrent_pre_save")
post_save.connect(torrent_post_save, sender=Torrent, dispatch_uid="torrent_post_save")


# Retreiving series names & urls ####################################

def series_update():
    # Retreive listing of series
    for (series_name, series_url) in get_series_url_dict().items():
        series, created = Series.objects.get_or_create(name=series_name)
        series.url = series_url
        series.save()

def get_series_url_dict():
    series = {}

    letter_list = get_dom_selection_from_url('.browseshowsdiv', 'http://www.kat.ph/tv/show/')
    for letter in letter_list:
        element_list = letter.cssselect('li')
        for element in element_list:
            series_url = element.cssselect("a")[0].get("href")
            series_name = normalize_series_name(element.cssselect("a")[0].text_content())
            series[series_name] = series_url
    
    return series

def normalize_series_name(name):
    return re.sub('\(.*\)', '', name)

def get_dom_selection_from_url(dom_selector, url):
    # Get HTML from URL
    br = mechanize.Browser()
    response = br.open(url)
    assert br.viewing_html()
    ungzipResponse(response, br)
    html_result = strip_script_tags(response.get_data())

    # DOM Select
    root = soupparser.fromstring(html_result)
    sel = CSSSelector(dom_selector)
    element = sel(root)

    return element

def ungzipResponse(r,b):
	headers = r.info()
	if 'Content-Encoding' in headers and headers['Content-Encoding']=='gzip':
		import gzip
		gz = gzip.GzipFile(fileobj=r, mode='rb')
		html = gz.read()
		gz.close()
		headers["Content-type"] = "text/html; charset=utf-8"
		r.set_data( html )
		b.set_response(r)

def strip_script_tags(html):
    stripped_html = (re.subn(r'<(script).*?</\1>(?s)', '', html)[0])
    return stripped_html

