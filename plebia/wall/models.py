# -*- coding: utf-8 -*-
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
from django.db.models import Q
from django import forms
from django.conf import settings

from wall.helpers import sane_text

import re, os


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Models ############################################################

# Torrent #############################

TORRENT_TYPES = (
    ('season', 'Full season'),
    ('episode', 'Single episode'),
)

TORRENT_STATUSES = (
    ('New', 'New'),
    ('Downloading metadata', 'Downloading metadata'),
    ('Paused metadata', 'Paused metadata'),
    ('Queued', 'Queued'),
    ('Downloading', 'Downloading'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
)

class ProcessingTorrentManager(models.Manager):
    def get_query_set(self):
        return super(ProcessingTorrentManager, self).get_query_set().filter(\
                Q(status='New') | \
                Q(status='Downloading metadata') | \
                Q(status='Paused metadata') | \
                Q(status='Queued') | \
                Q(status='Downloading'))

class CompletedTorrentManager(models.Manager):
    def get_query_set(self):
        return super(CompletedTorrentManager, self).get_query_set().filter(\
                Q(status='Completed'))

class ErrorTorrentManager(models.Manager):
    def get_query_set(self):
        return super(ErrorTorrentManager, self).get_query_set().filter(\
                Q(status='Error'))

class Torrent(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    hash = models.CharField('torrent hash/magnet', max_length=200, blank=True, unique=True)
    name = models.CharField('name', max_length=200, blank=True)
    type = models.CharField('type', max_length=20, choices=TORRENT_TYPES, blank=True)
    status = models.CharField('download status', max_length=20, choices=TORRENT_STATUSES, default='New')
    last_status_change = models.DateTimeField('date added', auto_now_add=True)
    progress = models.FloatField('download progress', default=0)
    seeds = models.IntegerField('seeds', null=True)
    peers = models.IntegerField('peers', null=True)
    download_speed = models.CharField('download speed', max_length=20, blank=True)
    upload_speed = models.CharField('upload speed', max_length=20, blank=True)
    eta = models.CharField('remaining download time', max_length=20, blank=True)
    active_time = models.CharField('active time', max_length=20, blank=True)
    details_url = models.CharField('url of detailled info', max_length=500, blank=True)
    tracker_url = models.CharField('url of tracker', max_length=500, blank=True)
    file_list = models.TextField('files in torrent (JSON)', blank=True)

    objects = models.Manager()
    processing_objects = ProcessingTorrentManager()
    completed_objects = CompletedTorrentManager()
    error_objects = ErrorTorrentManager()

    def __unicode__(self):
        return ("%s %s %s" % (self.name, self.hash, self.type))

    def get_magnet(self):
        '''Builds the magnet URL of the current torrent'''

        from urllib import quote

        magnet_link = 'magnet:?xt=urn:btih:%s' % self.hash
        if self.tracker_url:
            magnet_link += '&tr=%s' % quote(self.tracker_url)
        
        return magnet_link

    def set_status(self, new_status):
        '''Change the status of the torrent and update last_status_change timestamp'''

        from datetime import datetime

        self.status = new_status
        self.last_status_change = datetime.now()
        self.save()

    def is_timeout(self, delay):
        '''Check if the last change of status occured more than <delay> seconds ago'''

        from datetime import datetime, timedelta

        timeout_time = self.last_status_change + timedelta(seconds=delay)
        if datetime.now() > timeout_time:
            return True
        else:
            return False

    def update_from_torrent(self, torrent):
        '''Update status by copying attribute from another torrent
        Does not update the status or last_status_change.'''

        log.debug("Updating torrent %s from torrent %s", self, torrent)

        self.name = torrent.name
        self.progress = torrent.progress
        self.download_speed = torrent.download_speed
        self.upload_speed = torrent.upload_speed
        self.eta = torrent.eta
        self.active_time = torrent.active_time
        self.seeds = torrent.seeds
        self.peers = torrent.peers
        self.file_list = torrent.file_list

        self.save()

    def get_episode_video(self, episode):
        '''Locate a specific episode in a completed torrent'''

        from wall.packagemanager import MultiSeasonPackage, EpisodePackage

        log.info('Finding video for episode %s in torrent %s', episode, self)

        if self.type == 'season':
            package = MultiSeasonPackage(self)
        else:
            package = EpisodePackage(self)

        video = package.find_video(episode)
        
        return video


# Video ###############################

VIDEO_STATUSES = (
    ('New', 'New'),
    ('Queued', 'Queued'),
    ('Transcoding', 'Transcoding'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
    ('Not found', 'Not found'),
)

class ProcessingVideoManager(models.Manager):
    def get_query_set(self):
        return super(ProcessingVideoManager, self).get_query_set().filter(\
                Q(status='New') | \
                Q(status='Queued') | \
                Q(status='Transcoding'))

class CompletedVideoManager(models.Manager):
    def get_query_set(self):
        return super(CompletedVideoManager, self).get_query_set().filter(\
                Q(status='Completed'))

class ErrorVideoManager(models.Manager):
    def get_query_set(self):
        return super(ErrorVideoManager, self).get_query_set().filter(\
                Q(status='Not found') | \
                Q(status='Error'))

class VideoManager(models.Manager):
    def get_not_found_video(self):
        '''Returns a "Not found" Video object'''

        video = Video()
        video.status = 'Not found'
        video.save()
        return video

class Video(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    status = models.CharField('processing status', max_length=20, choices=VIDEO_STATUSES, default='New')
    original_path = models.CharField('file path (original)', max_length=500)
    webm_path = models.CharField('file path (WebM)', max_length=500, blank=True)
    mp4_path = models.CharField('file path (MP4)', max_length=500, blank=True)
    ogv_path = models.CharField('file path (OGV)', max_length=500, blank=True)
    image_path = models.CharField('file path (image)', max_length=500, blank=True)

    objects = VideoManager()
    processing_objects = ProcessingVideoManager()
    completed_objects = CompletedVideoManager()
    error_objects = ErrorVideoManager()

    def __unicode__(self):
        return ("%s %s" % (self.original_path, self.status))

    def start_transcoding(self):
        from wall.videotranscoder import VideoTranscoder
        video_transcoder = VideoTranscoder()

        if self.status == 'New':
            # Set paths
            prefix = self.original_path[:-4]
            self.webm_path = prefix + '.webm'
            self.mp4_path = prefix + '.mp4'
            self.ogv_path = prefix + '.ogv'
            self.image_path = prefix + '.jpg'

            # Thumb
            video_transcoder.generate_thumbnail(self.full_path(self.original_path), self.full_path(self.image_path))
            
            self.status = 'Queued'
            self.save()

        if self.status == 'Queued' and video_transcoder.has_free_slot():
            log.info('Starting transcoding of video %s', self)

            # WebM
            video_transcoder.transcode_webm(self.full_path(self.original_path), self.full_path(self.webm_path))

            self.status = 'Transcoding'
            self.save()

    def update_transcoding_status(self):
        '''Check if video transcoding is over'''

        from wall.videotranscoder import VideoTranscoder
        video_transcoder = VideoTranscoder()
        
        log.debug('Checking transcoding status of video %s', self)

        if self.status == 'Transcoding' and not video_transcoder.is_running(self.original_path):
            log.info('Transcoding finished for video %s', self)

            self.status = 'Completed'
            self.save()

    def full_path(self, relative_path):
        '''Give full system path of an internal stored path'''

        return os.path.join(settings.DOWNLOAD_DIR, relative_path)


# Series ##############################

class SeriesManager(models.Manager):

    def add_by_search(self, search_string):
        '''Retreiving series names for a given search string and creating any new Series objects'''
        
        log.info("Live search: '%s'", search_string)

        from thetvdbapi import TheTVDB
        tvdb = TheTVDB(settings.TVDB_API_KEY)
        tvdb_series_list = tvdb.get_matching_shows(search_string+'*')

        for tvdb_series in tvdb_series_list:
            log.info("Search result: '%s'", tvdb_series.name)

            # Check if the series already exists
            try:
                series = Series.objects.get(name=tvdb_series.name)
            except Series.DoesNotExist:
                # Check that we've got all the required tags
                if tvdb_series.name and tvdb_series.id and \
                        tvdb_series.language == 'en' and tvdb_series.banner_url:
                    log.info("Adding series to db: %s", tvdb_series.name)
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

        log.info("Updating series from TVDB (last update: %s)", update.time)

        (timestamp, series_list, episode_list) = tvdb.get_updates_by_timestamp(update.time)

        # Update series (details, seasons & episodes)
        for series_tvdb_id in series_list:
            try:
                series = Series.objects.get(tvdb_id=series_tvdb_id)
                # Check if this has been downloaded in the past
                if series.is_active():
                    log.info('Applying update to series "%s"', series.name)
                    series.update_from_tvdb()
            except Series.DoesNotExist:
                pass

        # Update individual episodes modifications (not new episodes)
        for episode_tvdb_id in episode_list:
            try:
                episode = Episode.objects.get(tvdb_id=episode_tvdb_id)
                episode_tvdb = tvdb.get_episode(episode_tvdb_id)
                log.info('Applying update to episode "%s s%de%d"', episode.season.series.name, episode.season.number, episode.number)
                episode.update_details(episode_tvdb)
            except Episode.DoesNotExist:
                pass

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
    overview = models.CharField('overview', max_length=1000, blank=True, null=True)
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

    def is_active(self):
        '''Check if series details (episodes, seasons...) need to be updated'''

        if self.nb_seasons() >= 1:
            return True
        else:
            return False

    def nb_seasons(self):
        '''Number of seasons currently attached'''

        nb_seasons = self.season_set.count()

        return nb_seasons

    def update_summary_details(self, tvdb_series):
        '''Update a part of the attributes based on tvdb object 
        (summary obtained through TheTVDB.get_matching_shows())'''

        self.name = sane_text(tvdb_series.name, length=200)
        self.tvdb_id = tvdb_series.id
        self.language = sane_text(tvdb_series.language, length=200)
        self.overview = sane_text(tvdb_series.overview, length=1000)
        self.first_aired = tvdb_series.first_aired
        self.imdb_id = sane_text(tvdb_series.imdb_id, length=50)
        self.banner_url = sane_text(tvdb_series.banner_url, length=200)

    def update_extended_details(self, tvdb_series):
        '''Update a part of the attributes based on tvdb object 
        (all details not obtained through TheTVDB.get_matching_shows())'''

        self.rating = tvdb_series.rating
        self.airing_status = sane_text(tvdb_series.status, length=50)
        self.poster_url = sane_text(tvdb_series.poster_url, length=200)
        self.fanart_url = sane_text(tvdb_series.fanart_url, length=200)
        self.tvcom_id = tvdb_series.tvcom_id
        self.zap2it_id = sane_text(tvdb_series.zap2it_id, length=200)
        self.tvdb_last_updated = tvdb_series.last_updated

    def update_episodes(self, tvdb_episode_list):
        '''Create/update season/episode objects as necessary based on a result set from TVDB'''

        for tvdb_episode in tvdb_episode_list:
            # Only get episodes in English to avoid duplicates
            if tvdb_episode.language == 'en':
                season_nb = tvdb_episode.season_number
                episode_nb = tvdb_episode.episode_number
                tvdb_id = tvdb_episode.id

                # Don't handle specials (season 0)
                if int(season_nb) and int(episode_nb):
                    season = Season.objects.get_or_create(series=self, number=season_nb)[0]

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

class ProcessingEpisodeManager(models.Manager):
    def get_query_set(self):
        return super(ProcessingEpisodeManager, self).get_query_set().filter(\
                Q(torrent__status='New') | \
                Q(torrent__status='Queued') | \
                Q(torrent__status='Downloading') | \
                Q(video__status='New') | \
                Q(video__status='Queued') | \
                Q(video__status='Transcoding'))

class CompletedEpisodeManager(models.Manager):
    def get_query_set(self):
        return super(CompletedEpisodeManager, self).get_query_set().filter(\
                Q(torrent__status='Completed'), \
                Q(video__status='Completed'))

class ErrorEpisodeManager(models.Manager):
    def get_query_set(self):
        return super(ErrorEpisodeManager, self).get_query_set().filter(\
                Q(torrent__status='Error') | \
                Q(video__status='Not found') | \
                Q(video__status='Error'))

class Episode(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    name = models.CharField('name', max_length=200, blank=True)
    season = models.ForeignKey(Season)
    torrent = models.ForeignKey(Torrent, null=True)
    video = models.ForeignKey(Video, null=True)
    tvdb_id = models.IntegerField('tvdb id')
    overview = models.CharField('overview', max_length=1000, blank=True)
    director = models.CharField('director', max_length=255, blank=True)
    guest_stars = models.CharField('guest stars', max_length=255, blank=True)
    language = models.CharField('language', max_length=50)
    rating = models.FloatField('rating', null=True)
    writer = models.CharField('writer', max_length=255, blank=True)
    first_aired = models.DateTimeField('first aired', null=True)
    image_url = models.CharField('image url', max_length=200, blank=True)
    imdb_id = models.CharField('imdb id', max_length=50, blank=True)
    tvdb_last_updated = models.DateTimeField('last updated on tvdb', null=True) 
    watched = models.BooleanField('watched', default=False)

    objects = models.Manager()
    processing_objects = ProcessingEpisodeManager()
    completed_objects = CompletedEpisodeManager()
    error_objects = ErrorEpisodeManager()

    def __unicode__(self):
        return ("%s (number %d)" % (self.season, self.number))

    def update_details(self, tvdb_episode):
        '''Update attributes based on a tvdb object'''

        self.tvdb_id = tvdb_episode.id
        self.name = sane_text(tvdb_episode.name, length=200)
        self.overview = sane_text(tvdb_episode.overview, length=1000)
        self.director = sane_text(tvdb_episode.director, length=255)
        self.guest_stars = sane_text(tvdb_episode.guest_stars, length=255)
        self.language = sane_text(tvdb_episode.language, length=50)
        self.rating = tvdb_episode.rating
        self.writer = sane_text(tvdb_episode.writer, length=255)
        self.first_aired = tvdb_episode.first_aired
        self.image_url = sane_text(tvdb_episode.image, length=200)
        self.imdb_id = sane_text(tvdb_episode.imdb_id, length=50)
        self.tvdb_last_updated = tvdb_episode.last_updated

    def get_or_create_torrent(self):
        '''Get the torrent for this episode (whether from the episode itself, its season or search). 
        Updates self.torrent accordingly.'''

        log.info("Trying to find the torrent for episode %s", self)

        # Check if we already have a torrent attached to this episode
        try:
            if self.torrent is not None:
                log.info("Torrent already found %s", self.season.torrent)
                return self.torrent
        except Torrent.DoesNotExist:
            pass

        # Check if there is a torrent for the full season
        try:
            if self.season.torrent is not None:
                log.info("Existing season torrent found %s", self.season.torrent)
                self.torrent = self.season.torrent
                self.save()

                return self.torrent
        except Torrent.DoesNotExist:
            pass

        # No torrent yet, need to search for one
        from wall.plugins import TorrentSearcher, get_active_plugin
        torrent_searcher = get_active_plugin(TorrentSearcher)
        try:
            self.torrent = torrent_searcher.search_torrent(self)
        except:
            log.exception("Error while searching for torrent for episode %s", self)
            self.torrent = Torrent(status='Error')
            self.torrent.save()
        self.save()

        # If it's a season torrent, register it on the season too
        if self.torrent.type == 'season':
            self.season.torrent = self.torrent
            self.season.save()
        
        if self.torrent.status == 'Error':
            log.warn('Could not find torrent for episode %s', self)
        else:
            log.info("Torrent search for episode %s returned %s", self, self.torrent)

        return self.torrent

    def get_or_create_video(self):
        '''Get the video for this episode, if there is a completed torrent'''

        # Check if the video has already been located for this torrent/episode
        if self.video is not None:
            log.info("Video already found %s", self.video)
            return self.video

        # Otherwise try to get it from the torrent file
        if self.torrent is not None and self.torrent.status == 'Completed':
            try:
                self.video = self.torrent.get_episode_video(self)
            except:
                log.exception("Error while searching for video for episode %s in torrent %s", self, self.torrent)
                self.video = Video(status='Error')
                self.video.save()
            self.save()

        if self.video.status == 'Error' or self.video.status == 'Not found':
            log.warn('Could not find video for episode %s in torrent %s', self, self.torrent)
        else:
            log.info("Video search for episode %s returned %s", self, self.video)

        return self.video

    def next_episode(self):
        pass

    def previous_episode(self):
        pass


# Post ################################

class Post(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    series = models.ForeignKey(Series)
    
    def __unicode__(self):
        return ("%s" % (self.series))


# TVDBCache ################################

class TVDBCache(models.Model):
    type = models.CharField('update type', max_length=20)
    time = models.IntegerField('update time')
    
    def __unicode__(self):
        return ("%s = %d" % (self.type, self.time))



# Forms #############################################################

class PostForm(forms.Form):
    name = forms.CharField(max_length=200)






