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
from django.conf import settings

import re

# Models ############################################################

# Torrent #############################

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

class Torrent(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    hash = models.CharField('torrent hash/magnet', max_length=200)
    name = models.CharField('name', max_length=200, blank=True)
    type = models.CharField('type', max_length=20, choices=TORRENT_TYPES)
    status = models.CharField('download status', max_length=20, choices=TORRENT_STATUSES, default='New')
    progress = models.FloatField('download progress', default=0)
    seeds = models.IntegerField('seeds')
    peers = models.IntegerField('peers')
    download_speed = models.CharField('download speed', max_length=20, blank=True)
    upload_speed = models.CharField('upload speed', max_length=20, blank=True)
    eta = models.CharField('remaining download time', max_length=20, blank=True)

    def __unicode__(self):
        return ("%s %s %s" % (self.name, self.hash, self.type))


# Video ###############################

VIDEO_STATUSES = (
    ('New', 'New'),
    ('Transcoding', 'Transcoding'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
)

class Video(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    status = models.CharField('processing status', max_length=20, choices=VIDEO_STATUSES, default='New')
    original_path = models.CharField('file path (original)', max_length=200)
    webm_path = models.CharField('file path (WebM)', max_length=200, blank=True)
    mp4_path = models.CharField('file path (MP4)', max_length=200, blank=True)
    ogv_path = models.CharField('file path (OGV)', max_length=200, blank=True)
    image_path = models.CharField('file path (image)', max_length=200, blank=True)

    def __unicode__(self):
        return ("%s %s" % (self.original_path, self.status))


# Series ##############################

class SeriesManager(models.Manager):

    def add_by_search(self, search_string):
        '''Retreiving series names for a given search string and creating any new Series objects'''
        from thetvdbapi import TheTVDB
        tvdb = TheTVDB(settings.TVDB_API_KEY)
        
        tvdb_series_list = tvdb.get_matching_shows(search_string+'*')
        for tvdb_series in tvdb_series_list:
            # Check if the series already exists
            try:
                series = Series.objects.get(name=tvdb_series.name)
            except Series.DoesNotExist:
                # Check that we've got all the required tags
                if tvdb_series.name and tvdb_series.id and \
                        tvdb_series.language == 'en' and tvdb_series.banner_url:
                    # Then create the local series object 
                    series = Series()
                    series.update_summary_details(tvdb_series)
                    series.save()

    def apply_tvdb_updates(self):
        '''Retreives last updates from TVDB and update existing series/seasons/episodes 
        accordingly'''

        from thetvdbapi import TheTVDB
        tvdb = TheTVDB(settings.TVDB_API_KEY)

        try:
            update = TVDBCache.objects.get(type='last')
        except TVDBCache.DoesNotExist:
            server_time = tvdb.get_server_time()
            update = TVDBCache(type='last', time=server_time)
            update.save()
            return False

        (timestamp, series_list, episode_list) = tvdb.get_updates_by_timestamp(update.time)

        # Update series (details, seasons & episodes)
        for series_tvdb_id in series_list:
            try:
                series = Series.objects.get(tvdb_id=series_tvdb_id)
            except Series.DoesNotExist:
                pass

            series.update_from_tvdb()

        # Update individual episodes modifications (not new episodes)
        for episode_tvdb_id in episode_list:
            try:
                episode = Episode.objects.get(tvdb_id=episode_tvdb_id)
            except Episode.DoesNotExist:
                pass

            episode_tvdb = tvdb.get_episode(episode_tvdb_id)
            episode.update_details(episode_tvdb)

        # Update timestamp
        update.time = timestamp
        update.save()


class Series(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    name = models.CharField('name', max_length=200)
    banner_url = models.CharField('banner url', max_length=200)
    tvdb_id = models.IntegerField('tvdb id')
    imdb_id = models.CharField('imdb id', max_length=50, blank=True, null=True)
    language = models.CharField('language', max_length=50)
    overview = models.CharField('overview', max_length=500, blank=True)
    first_aired = models.DateTimeField('first aired', null=True)
    rating = models.FloatField('rating', null=True)
    airing_status = models.CharField('airing status', max_length=50, blank=True)
    poster_url = models.CharField('poster url', max_length=200, blank=True)
    fanart_url = models.CharField('fan art url', max_length=200, blank=True)
    tvcom_id = models.IntegerField('tv.com id', null=True)
    zap2it_id = models.CharField('zap2it id', max_length=200, blank=True)
    tvdb_last_updated = models.DateTimeField('date added', null=True)

    objects = SeriesManager()

    def __unicode__(self):
        return ("%s" % (self.name))

    def update_from_tvdb(self):
        '''Fetch all available information about a series from tvdb'''

        from thetvdbapi import TheTVDB

        tvdb = TheTVDB(settings.TVDB_API_KEY)
        (tvdb_series, tvdb_episode_list) = tvdb.get_show_and_episodes(self.tvdb_id)

        self.update_summary_details(tvdb_series)
        self.update_extended_details(tvdb_series)
        self.update_episodes(tvdb_episode_list)
        self.save()

    def update_summary_details(self, tvdb_series):
        '''Update a part of the attributes based on tvdb object 
        (summary obtained through TheTVDB.get_matching_shows())'''

        self.name = tvdb_series.name
        self.tvdb_id = tvdb_series.id
        self.language = tvdb_series.language
        self.overview = tvdb_series.overview
        self.first_aired = tvdb_series.first_aired
        self.imdb_id = tvdb_series.imdb_id
        self.banner_url = tvdb_series.banner_url

    def update_extended_details(self, tvdb_series):
        '''Update a part of the attributes based on tvdb object 
        (all details not obtained through TheTVDB.get_matching_shows())'''

        self.rating = tvdb_series.rating
        self.airing_status = tvdb_series.status
        self.poster_url = tvdb_series.poster_url
        self.fanart_url = tvdb_series.fanart_url
        self.tvcom_id = tvdb_series.tvcom_id
        self.zap2it_id = tvdb_series.zap2it_id
        self.tvdb_last_updated = tvdb_series.last_updated

    def update_episodes(self, tvdb_episode_list):
        '''Create/update season/episode objects as necessary based on a result set from TVDB'''

        for tvdb_episode in tvdb_episode_list:
            # Only get episodes in English to avoid duplicates
            if tvdb_episode.language == 'en':
                season_nb = tvdb_episode.season_number
                tvdb_id = tvdb_episode.id

                # Don't handle specials (season 0)
                if int(season_nb):
                    season = Season.objects.get_or_create(series=self, number=season_nb)[0]

                    episode_nb = tvdb_episode.episode_number
                    episode = Episode.objects.get_or_create(season=season, number=episode_nb, tvdb_id=tvdb_id)[0]

                    episode.update_details(tvdb_episode)
                    episode.save()


# Season ##############################

class Season(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    series = models.ForeignKey(Series)
    torrent = models.ForeignKey(Torrent, null=True)
    
    def __unicode__(self):
        return ("%s (season %s)" % (self.series, self.number))


# Episode #############################

class Episode(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    name = models.CharField('name', max_length=200, blank=True)
    season = models.ForeignKey(Season)
    torrent = models.ForeignKey(Torrent, null=True)
    video = models.ForeignKey(Video, null=True)
    tvdb_id = models.IntegerField('tvdb id')
    overview = models.CharField('overview', max_length=500, blank=True)
    director = models.CharField('director', max_length=50, blank=True)
    guest_stars = models.CharField('guest stars', max_length=50, blank=True)
    language = models.CharField('language', max_length=50)
    rating = models.FloatField('rating', null=True)
    writer = models.CharField('writer', max_length=50, blank=True)
    first_aired = models.DateTimeField('first aired', null=True)
    image_url = models.CharField('image url', max_length=200, blank=True)
    imdb_id = models.CharField('imdb id', max_length=50, blank=True)
    tvdb_last_updated = models.DateTimeField('last updated on tvdb', null=True) 
    watched = models.BooleanField('watched', default=False)

    def __unicode__(self):
        return ("%s (number %d)" % (self.season, self.number))

    def update_details(self, tvdb_episode):
        '''Update attributes based on a tvdb object'''

        self.tvdb_id = tvdb_episode.id
        self.name = tvdb_episode.name
        self.overview = tvdb_episode.overview
        self.director = tvdb_episode.director
        self.guest_stars = tvdb_episode.guest_stars
        self.language = tvdb_episode.language
        self.rating = tvdb_episode.rating
        self.writer = tvdb_episode.writer
        self.first_aired = tvdb_episode.first_aired
        self.image_url = tvdb_episode.image
        self.imdb_id = tvdb_episode.imdb_id
        self.tvdb_last_updated = tvdb_episode.last_updated

    def start_download(self):
        '''Start actually retreiving the torrent & video'''
        
        from plebia.wall import videoutils

        if self.torrent is None:
            self.torrent = self.get_or_create_torrent()
            self.create_video_if_completed()
            self.save()

    def on_torrent_saved(self):
        '''Called every time the torrent object for this episode is saved'''

        self.create_video_if_completed()        

    def create_video_if_completed(self):
        '''Create video object when the torrent download is completed'''

        from plebia.wall import videoutils

        if self.torrent.status == 'Completed' and self.video is None:
            self.video = videoutils.locate_video(self)
            self.save()

    def get_or_create_torrent(self):
        from plebia.wall import torrentutils

        season = self.season
        series = season.series

        # Check if the full season is not already there
        if season.torrent is not None:
            torrent = season.torrent
        else:
            # Episode
            search_string = "(tv|television) %s s%02de%02d" % (series.name, season.number, self.number)
            episode_torrent = torrentutils.get_torrent_by_search(search_string)
            # Season
            search_string = "(tv|television) %s season %d" % (series.name, season.number)
            season_torrent = torrentutils.get_torrent_by_search(search_string)

            # See if we should prefer the season or the episode
            if season_torrent is None and episode_torrent is None:
                return None
            elif season_torrent is None \
                    or season_torrent.seeds < 10:
                torrent = episode_torrent
                torrent.type = 'episode'
                torrent.save()
            elif episode_torrent is None \
                    or episode_torrent.seeds < 10 \
                    or episode_torrent.seeds*10 < season_torrent.seeds:
                torrent = season_torrent
                torrent.type = 'season'
                torrent.save()
                season.torrent = torrent
                season.save()
            else:
                torrent = episode_torrent
                torrent.type = 'episode'
                torrent.save()

        return torrent

    def next_episode(self):
        pass

    def previous_episode(self):
        pass


# PredictiveDownloadManager ###########

class PredictiveDownloadManager:
    '''Manages auto-start of episodes download'''

    def on_episode_created(self, episode):
        '''Called every time an episode object is created'''
        pass

    def on_episode_updated(self, episode):
        '''Called every time an episode object is updated (all saves except creation)'''
        pass
    
    def on_post_created(self, episode):
        '''Called every time a post object is created'''
        pass


# Post ################################

class Post(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    series = models.ForeignKey(Series)
    
    def __unicode__(self):
        return ("%s" % (self.series))


# TVDBCache ################################

class TVDBCache(models.Model):
    type = models.IntegerField('update type')
    time = models.IntegerField('update time')
    
    def __unicode__(self):
        return ("%s = %d" % (self.type, self.time))



# Forms #############################################################

class PostForm(forms.Form):
    name = forms.CharField(max_length=200)


# Signals ###########################################################

def torrent_post_save(sender, **kwargs):
    torrent = kwargs['instance']
    created = kwargs['created']

    # Notify all episodes linked to this torrent
    episode_list = torrent.episode_set.all()
    for episode in episode_list:
        episode.on_torrent_saved()

def episode_post_save(sender, **kwargs):
    episode = kwargs['instance']
    created = kwargs['created']

    # Notify predictive download manager
    manager = PredictiveDownloadManager()
    if created:
        manager.on_episode_created(episode)
    else:
        manager.on_episode_updated(episode)

def post_post_save(sender, **kwargs):
    post = kwargs['instance']
    created = kwargs['created']

    # Notify predictive download manager
    manager = PredictiveDownloadManager()
    if created:
        manager.on_post_created(post)


# Register signal handlers
post_save.connect(torrent_post_save, sender=Torrent, dispatch_uid="torrent_post_save")
post_save.connect(episode_post_save, sender=Episode, dispatch_uid="episode_post_save")
post_save.connect(post_post_save, sender=Post, dispatch_uid="post_post_save")


                        




