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

from django.test import TestCase
from django.conf import settings

from plebia.log import get_logger
from wall.models import *
from wall.plugins import *
from wall.helpers import mkdir_p
from cache import get_cache, set_cache

from mock import Mock, patch
import json
import os, shutil


# Tests #############################################################

# TODO Test API along the way

class PlebiaTest(TestCase):
    #fixtures = ['video.json']

    def test_raise_exception_upon_error_critical_log(self):
        '''Make sure exceptions are raised upon ERROR or CRITICAL log messages'''

        self.assertEqual(settings.RAISE_EXCEPTION_ON_ERROR, True, "To run the tests, RAISE_EXCEPTION_ON_ERROR must be set to True in the settings, otherwise some exceptions might go unnoticed")

        log = get_logger(__name__)
        exception_raised = False
        try:
            log.error('Test error log message')
        except:
            exception_raised = True

        self.assertEqual(exception_raised, True)

    def api_check(self, model, id, value_dict):
        '''Helper method to check values against the values returned by the API'''

        # Get JSON object from API
        api_url = "/api/v1/%s/%d/" % (model, id)
        c = self.client
        response = c.get(api_url)

        if value_dict is None:
            # Check that the entry doesn't exist
            self.assertEqual(response.status_code, 410) # "Gone" / No such object
        else:
            self.assertEqual(response.status_code, 200, "%s: %s" % (response.status_code, response.content)) # code 410 = object not found
            api_dict = json.loads(response.content)
            # Check each value in the provided dictionary to ensure they match the ones from the API object
            for (key, value) in value_dict.items():
                self.assertEqual(api_dict[key], value)

    def test_000_home(self):
        c = self.client
        response = c.get("/")
        self.assertEqual(response.status_code, 200)

    def create_fake_season(self, name="Test"):
        series = Series.objects.get_or_create(name=name, tvdb_id=1)[0]
        season = Season.objects.get_or_create(number=2, series=series)[0]
        return season

    def create_torrent_dir(self, name):
        '''Create torrent directory in the test download dir'''

        mkdir_p(settings.TEST_DOWNLOAD_DIR)
        mkdir_p(os.path.join(settings.TEST_DOWNLOAD_DIR, name))
        settings.DOWNLOAD_DIR = settings.TEST_DOWNLOAD_DIR

    def create_fake_torrent(self, name="Test", status="Downloading", type="episode"):
        # Fake the newly downloaded torrent
        torrent = Torrent()
        torrent.hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent.name = name
        torrent.type = type
        torrent.status = status
        torrent.seeds = 10
        torrent.peers = 10
        torrent.save()

        self.create_torrent_dir(torrent.name)

        return torrent

    def test_video_not_found_in_episode_torrent(self):
        """When an episode torrent is successfully downloaded, but the video for this episode can't be found"""

        # Fake episode & post
        name = 'Test episode not found in season'
        episode = Episode(number=10, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name)
        episode.torrent.status = 'Completed'
        episode.torrent.save()
        episode.save()

        episode.get_or_create_video()

        # Directory is empty so video should be marked as not found
        self.api_check('video', 1, {'status': 'Not found'})

    def test_video_not_found_in_season_torrent(self):
        """When a season torrent is successfully downloaded, but the video for this episode can't be found"""

        # Fake episode & post
        name = 'Test episode not found in season'
        episode = Episode(number=10, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type='season')
        episode.torrent.status = 'Completed'
        episode.torrent.save()
        episode.save()

        episode.get_or_create_video()

        # Directory is empty so video should be marked as not found
        self.api_check('video', 1, {'status': 'Not found'})

    def init_test_torrent_directory(self, name):
        '''Creates/recreates an empty test directory'''

        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        shutil.rmtree(torrent_dir, ignore_errors=True)
        os.mkdir(torrent_dir)
        return torrent_dir

    def clear_test_directory(self):
        '''Make sure the test directory is empty (rm/mkdir)'''
        shutil.rmtree(settings.TEST_DOWNLOAD_DIR, ignore_errors=True)
        os.mkdir(settings.TEST_DOWNLOAD_DIR)

    def test_find_video_in_multiple_seasons_torrent(self):
        # Fake episode
        name = 'Test multiple seasons'
        episode = Episode(number=10, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type='season', status='Completed')
        episode.save()

        # Build directory with multiple folders, one for each season
        torrent_dir = self.init_test_torrent_directory(episode.torrent.name)
        os.mkdir(os.path.join(torrent_dir, 'SeaSon2'))
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, 'SeaSon2', 'S02E10.avi'))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, 'SeaSon2', 'S02E10.avi') })

    def test_find_single_episode_in_season_torrent_subfolder(self):
        """When a season torrent has one season, but all its episodes contained in a subfolder"""

        # Fake episode
        name = 'Test episode name within season torrent subfolder'
        filename = 'Test - 201 - Title.avi'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="season", status='Completed')
        episode.save()

        # Copy test file to episode name to test
        torrent_dir = self.init_test_torrent_directory(episode.torrent.name)
        torrent_dir = os.path.join(torrent_dir, 'sub folder')
        os.mkdir(torrent_dir)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, filename))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, 'sub folder', filename) })

    def test_find_single_episode_in_episode_torrent_subfolder_with_two_videos(self):
        """When an episode has its video contained in a folder, with a sample (smaller) video too in a subfolder"""

        # Fake episode
        name = 'Test folder'
        filename = 'Test.avi'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="episode", status='Completed')
        episode.save()

        # Copy test file to episode name to test
        torrent_dir = self.init_test_torrent_directory(name)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, filename))

        # Copy sample video, which is smaller
        torrent_dir = os.path.join(torrent_dir, 'sample')
        os.mkdir(torrent_dir)
        shutil.copy2(settings.TEST_SHORT_VIDEO_PATH, os.path.join(torrent_dir))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, filename) })

    def test_find_single_episode_in_single_file_season_torrent_error(self):
        """When an season torrent is a single file, fail racefully when looking for a single episode"""

        filename='Test.avi'

        # Fake episode
        episode = Episode(number=1, tvdb_id=1, name='Test episode')
        episode.season = self.create_fake_season(name='Test series')
        episode.torrent = Torrent(hash='aaaa', name=filename, type='season', status='Completed')
        episode.torrent.save()
        episode.save()

        # Create torrent file
        mkdir_p(settings.TEST_DOWNLOAD_DIR)
        settings.DOWNLOAD_DIR = settings.TEST_DOWNLOAD_DIR
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(settings.TEST_DOWNLOAD_DIR, filename))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'Not found' })

    def _test_find_single_episode_in_season_torrent(self, name, number, filename, episode_name="The great episode"):
        """Helper method, to test finding a single episode name inside a season torrent
        The episode 'number' argument should be 1 on first call within same test method, and increase by 1 each call"""

        # Fake episode
        episode = Episode(number=number, tvdb_id=number, name=episode_name)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="season", status='Completed')
        episode.save()

        # Copy test file to episode name to test
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, filename))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', number, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, filename) })

    def create_fake_video(self, name, video_filename):
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, video_filename))

    def test_find_episodes_in_season_torrent(self):
        """Match episodes against their number inside a season torrent"""

        self.clear_test_directory()
        name = u'Test find episode in season'
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        os.mkdir(torrent_dir)

        self._test_find_single_episode_in_season_torrent(name, 1, u's02e01.avi')
        self._test_find_single_episode_in_season_torrent(name, 2, u'S02E02.avi')
        self._test_find_single_episode_in_season_torrent(name, 3, u's2e3.avi')
        self._test_find_single_episode_in_season_torrent(name, 4, u'204.avi')
        self._test_find_single_episode_in_season_torrent(name, 5, u'0205.avi')
        self._test_find_single_episode_in_season_torrent(name, 6, u'Season 2 - Episode 6.avi')
        self._test_find_single_episode_in_season_torrent(name, 7, u'season 02 episode 07.avi')
        self._test_find_single_episode_in_season_torrent(name, 8, u'02x08.avi')
        self.create_fake_video(name, u'S02E90.avi') # Create potential false positives
        self.create_fake_video(name, u's2e90.avi')
        self._test_find_single_episode_in_season_torrent(name, 9, u'[2.09].avi')
        self._test_find_single_episode_in_season_torrent(name, 10, u'[2x10].avi')
        self._test_find_single_episode_in_season_torrent(name, 11, u's02e11.m4v') # Unknown on some mime.types files
        self._test_find_single_episode_in_season_torrent(name, 12, u'Test 2-12.avi')
        self._test_find_single_episode_in_season_torrent(name, 13, u'Test s02 e13.avi')
        self._test_find_single_episode_in_season_torrent(name, 14, u'Test (2x14 Test) test.avi')
        self._test_find_single_episode_in_season_torrent(name, 15, u'Test (2x15 Test) testó.avi') # Unicode
        self._test_find_single_episode_in_season_torrent(name, 16, u'episode.with-only_title.avi', episode_name='Episode with only title')
        self._test_find_single_episode_in_season_torrent(name, 17, u'Test - S2 E17 - Episode.avi')
        self._test_find_single_episode_in_season_torrent(name, 18, u'18 - Episode.avi')
        self._test_find_single_episode_in_season_torrent(name, 19, u'19 - Episode.rmvb')
        self._test_find_single_episode_in_season_torrent(name, 20, u'Series - 20 - Episode.avi')

    def test_find_single_episode_in_episode_torrent_dir(self):
        """Episode torrent with video contained in a directory"""

        self.clear_test_directory()

        # Fake episode
        name = 'Test - 201 - Title'
        filename = '%s.avi' % name
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="torrent", status='Completed')
        episode.save()

        # Copy test file to episode name to test
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(settings.TEST_DOWNLOAD_DIR, name, filename))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(name, filename) })

    def test_find_single_episode_in_episode_torrent(self):
        """Episode torrent as a single file video"""

        self.clear_test_directory()

        # Fake episode
        name = 'Test episode single video file'
        filename = '%s - 201 - Title.avi' % name
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=filename, type="torrent", status='Completed')
        episode.save()

        # Copy test file to episode name to test
        shutil.rmtree(os.path.join(settings.TEST_DOWNLOAD_DIR, filename), ignore_errors=True)
        shutil.copyfile(settings.TEST_VIDEO_PATH, os.path.join(settings.TEST_DOWNLOAD_DIR, filename))

        episode.get_or_create_video()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': filename })

    def build_isohunt_result(self, torrent_dict_array):
        """Builds and returns a IsoHunt result string. torrent_dict_array=[{'name':'Torrent name', 'hash':'aaaa', 'seeds':10, 'peers':20}, ...]"""

        result = u"""{"title": "","link": "http://isohunt.com","description": "BitTorrent Search","language": "en-us","category": "TV","max_results": 1000,"ttl": 15,"image": {"title": "","url": "http://isohunt.com/img/buttons/isohunt-02.gif","link": "http://isohunt.com/","width": 157,"height": 45}, "lastBuildDate": "Tue, 01 Nov 2011 12:01:51 GMT","pubDate": "Tue, 01 Nov 2011 12:01:51 GMT","total_results":2, "censored":0, "items": {"list": ["""

        for torrent_dict in torrent_dict_array:
            result += u"""{"title":"%s","link":"http:\/\/isohunt.com\/torrent_details","guid":"213882961","enclosure_url":"http://ca.isohunt.com/download/213882961/","length":379895939,"tracker":"tracker.openbittorrent.com","tracker_url":"http:\/\/tracker.openbittorrent.com:80\/announce","kws":"","exempts":"","category":"TV","original_site":"original.com","original_link":"http:\/\/original.com\/torrent","size":"362.3 MB","files":10,"Seeds":%d,"leechers":%d,"downloads":671,"votes":0,"comments":0,"hash":"%s","pubDate":"Sun, 04 Jul 2010 17:28:51 GMT"},""" % (torrent_dict['name'], torrent_dict['seeds'], torrent_dict['peers'], torrent_dict['hash'])

        result = result[:-1] # Remove trailing ','
        result += u"]}}" # Close

        return result

    @patch('wall.helpers.get_url')
    def run_isohunt_search(self, episode, episode_result, season_result, mock_get_url):
        '''Run plugin code for searching torrent, based on mock isoHunt results'''
        
        # Return different values for the two calls to the search engine (first: episode, second: season)
        values = [season_result, episode_result]
        def side_effect(url):
            return values.pop()
        mock_get_url.side_effect = side_effect
        
        searcher = IsoHuntSearcher()
        searcher.search_torrent(episode)

    @patch('wall.helpers.get_url')
    def test_torrent_search_isohunt_empty_result(self, mock_get_url):
        '''Handle empty result sets gracefully'''

        mock_get_url.return_value = """{"title": "isoHunt", "link": "http://isohunt.com", "description": "BitTorrent Search", "language": "en-us", "category": "TV", "max_results": 1000, "ttl": 15, "image": {"title": "isoHunt", "url": "http://isohunt.com/", "link": "http://isohunt.com/", "width": 157, "height": 45}, "lastBuildDate": "Sun, 06 Nov 2011 15:54:15 GMT","pubDate": "Sun, 06 Nov 2011 15:54:15 GMT","total_results":0, "censored":0}"""

        searcher = IsoHuntSearcher()
        torrent = searcher.search_torrent_by_string('Test series', None)

        self.assertEqual(torrent, None)

    def test_torrent_search_isohunt_only_season_minimum_seeds(self):
        '''Select season torrent from search results when only the season has the minimum number of seeds required'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        # Fake the results from the search engine
        episode_result = self.build_isohunt_result([{'name':'Unrelated result', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' s02e01', 'hash': 'good episode hash', 'seeds':1, 'peers':100}])
        season_result  = self.build_isohunt_result([{'name':'Unrelated result', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' season 2', 'hash': 'good season hash', 'seeds':10, 'peers':2}])
        
        self.run_isohunt_search(episode, episode_result, season_result)

        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'good season hash', 'seeds': 10, 'peers': 2})

    def test_torrent_search_isohunt_only_episode_minimum_seeds(self):
        '''Select episode torrent from search results when only the episode has the minimum number of seeds required'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        # Fake the results from the search engine
        episode_result = self.build_isohunt_result([{'name':'Unrelated result s02e01', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' s02e01', 'hash': 'good episode hash', 'seeds':10, 'peers':1}])
        season_result  = self.build_isohunt_result([{'name':'Unrelated result', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' season 2', 'hash': 'good season hash', 'seeds':1, 'peers':20}])
        
        self.run_isohunt_search(episode, episode_result, season_result)

        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'episode', 'hash': 'good episode hash', 'seeds': 10, 'peers': 1})

    def test_torrent_search_isohunt_season_more_seeds(self):
        '''Select season torrent from search results when the season has much more seeds'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        # Fake the results from the search engine
        episode_result = self.build_isohunt_result([{'name':'Unrelated result s02e01', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' s02e01', 'hash': 'good episode hash', 'seeds':13, 'peers':2000}])
        season_result  = self.build_isohunt_result([{'name':'Unrelated result', 'hash': 'wrong hash', 'seeds':100, 'peers':1000}, \
                                                    {'name':name+' season 2', 'hash': 'good season hash', 'seeds':150, 'peers':20}])
        
        self.run_isohunt_search(episode, episode_result, season_result)

        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'good season hash', 'seeds': 150})

    def test_torrent_search_isohunt_other_series_with_longer_name(self):
        '''Select season torrent from search results when a result is about another series whose name contain the searched series name'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        # Series with similar name
        similar_name = 'test series reloaded'
        self.create_fake_season(name=similar_name)

        # Fake the results from the search engine
        episode_result = self.build_isohunt_result(list())
        season_result  = self.build_isohunt_result([{'name':similar_name+' season 2', 'hash': 'wrong hash', 'seeds':150, 'peers':1000}, \
                                                    {'name':        name+' season 2', 'hash': 'good hash',  'seeds':5,   'peers':20}])
        
        self.run_isohunt_search(episode, episode_result, season_result)

        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'good hash'})

    @patch.object(TorrentSearcher, 'search_series_torrent')
    @patch.object(TorrentSearcher, 'search_season_torrent')
    @patch.object(TorrentSearcher, 'search_episode_torrent')
    def test_torrent_search_series_when_no_season_and_no_episode(self, mock_search_episode_torrent, mock_search_season_torrent, mock_search_series_torrent):
        '''Also try to search for the series without a season/episode number when the rest has failed'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        # Even with two seasons
        Season(series=episode.season.series, number=3).save()

        series_torrent = Torrent(hash='good hash', seeds=5, peers=20, type='season')

        mock_search_episode_torrent.return_value = None
        mock_search_season_torrent.return_value = None
        mock_search_series_torrent.return_value = series_torrent

        searcher = TorrentSearcher()
        searcher.search_torrent(episode)
        
        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'good hash'})

    @patch.object(TorrentSearcher, 'search_series_torrent')
    @patch.object(TorrentSearcher, 'search_season_torrent')
    @patch.object(TorrentSearcher, 'search_episode_torrent')
    def test_torrent_search_chose_episode_over_series(self, mock_search_episode_torrent, mock_search_season_torrent, mock_search_series_torrent):
        '''Searching for the series should not prevent from chosing the episode alone, which should be prefered if it exists'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        episode_torrent = Torrent(hash='good hash', seeds=5, peers=20, type='episode')
        series_torrent = Torrent(hash='wrong hash', seeds=500, peers=2000, type='season')

        mock_search_episode_torrent.return_value = episode_torrent
        mock_search_season_torrent.return_value = None
        mock_search_series_torrent.return_value = series_torrent

        searcher = TorrentSearcher()
        searcher.search_torrent(episode)
        
        # Check state
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'episode', 'hash': 'good hash'})

    @patch.object(TorrentSearcher, 'search_torrent_by_string')
    def test_torrent_search_remove_special_chars(self, mock_search_torrent_by_string):
        '''Special characters should be removed from the search strings'''

        # Fake episode
        name = 'Test: series.'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        mock_search_torrent_by_string.return_value = None

        searcher = TorrentSearcher()
        searcher.search_torrent(episode)
        
        # Check state
        mock_search_torrent_by_string.assert_called_with('Test series', None)

    @patch.object(TorrentSearcher, 'search_torrent_by_string')
    def test_torrent_search_with_different_season_number_types(self, mock_search_torrent_by_string):
        '''Search different formatings for season number'''

        # Fake episode
        name = 'Test series'
        episode = Episode(number=1, tvdb_id=1)
        episode.season = self.create_fake_season(name=name)
        episode.save()

        called_with = list()
        def side_effect(name, episode_string):
            called_with.append(episode_string)
            return None
        mock_search_torrent_by_string.side_effect = side_effect

        searcher = TorrentSearcher()
        searcher.search_torrent(episode)
        
        # Check that all required searches have been done
        for episode_string in ['season 2', 'season two']:
            if episode_string not in called_with:
                self.assertTrue(False, 'No search done for "%s"' % episode_string)

    @patch('wall.plugins.get_active_plugin')
    def test_torrent_search_when_season_torrent_already_found(self, mock_get_active_plugin):
        '''When a season torrent already exist, use it for episodes of this season'''

        name = 'Test series'

        # Fake episode 1, which will trigger getting the full season
        episode1 = Episode(number=1, tvdb_id=1)
        episode1.season = self.create_fake_season(name=name)
        episode1.save()
        # Fake episode 2, which should use the existing season torrent
        episode2 = Episode(number=2, tvdb_id=2, season=episode1.season)
        episode2.save()

        # Setup a fake search plugin
        mock_plugin = Mock()
        mock_get_active_plugin.return_value = mock_plugin

        # Search - episode 1 torrent
        torrent = Torrent(hash='good hash', type='season')
        torrent.save()
        mock_plugin.search_torrent.return_value = torrent
        episode1.get_or_create_torrent()
        # Check state
        self.assertEqual(episode1.torrent.id, 1)
        self.assertEqual(episode1.torrent.hash, 'good hash')
        self.assertEqual(episode1.season.torrent.id, 1)

        # Search - episode 2 torrent
        mock_get_active_plugin.search_torrent.return_value = None
        episode2.get_or_create_torrent()
        # Check state
        self.assertEqual(episode2.torrent.id, 1)

    def select_plugin(self, plugin_point, plugin_name):
        '''Make the specified plugin the only one active for a given plugin point'''

        from djangoplugins.models import ENABLED, DISABLED

        for plugin in plugin_point.get_plugins_qs():
            if plugin.name == plugin_name:
                plugin.status = ENABLED
            else:
                plugin.status = DISABLED
            plugin.save()

    @patch('wall.videotranscoder.VideoTranscoder')
    def test_series_processing(self, mock_video_transcoder):
        '''Fake download of a list of test series to process and get success rates on'''

        import wall.plugins, wall.thetvdbapi, wall.helpers

        # Don't pollute the real download dir
        settings.DOWNLOAD_DIR = settings.TEST_DOWNLOAD_DIR

        default_open_url = None
        default_update_queued_torrents = None
        default_get_url = None
        default_get_torrent_info_for_hash = None
        default_add_magnet = None
        default_remove_hash = None

        # FIXME: Tests should cover all plugins
        self.select_plugin(TorrentSearcher, 'torrentz-searcher')

        # Don't let the other tests continue without reverting to the default methods/objects
        # we override in this test
        try:
            #### Retreive TVDB data for test strings ####

            # Cache it to allow to run this test multiple consecutive times quickly, without 
            # having to query the db engine every time
            def open_url(url):
                url_id = url.replace('/', '_')
                cache_path = os.path.join(settings.CACHE_DIR, url_id)

                # TVDB's parsing really wants a fp to an actual file
                # Instead of using get/set_cache, prepare the file directly
                mkdir_p(settings.CACHE_DIR)
                if not os.path.isfile(cache_path):
                    cache_fp = default_open_url(url)
                    with open(cache_path, 'w') as f:
                        f.write(cache_fp.read())

                return open(cache_path)

            default_open_url = wall.helpers.open_url
            wall.helpers.open_url = open_url

            for series_name in settings.TEST_SERIES_LIST:
                # Retreive series info
                Series.objects.add_by_search(series_name)
                
                # Make series active (scheduled for download)
                series = Series.objects.get(name=series_name)
                series.update_from_tvdb()


            #### Torrent search ####

            from wall.downloadmanager import DownloadManager

            def get_url(url, sleep_time=2):
                url_id = url.replace('/', '_')
                cached_content = get_cache(url_id)
                if cached_content:
                    return cached_content
                else:
                    content = default_get_url(url, sleep_time=sleep_time)
                    set_cache(url_id, content)
                    return content

            default_get_url = wall.helpers.get_url
            wall.helpers.get_url = get_url

            download_manager = DownloadManager()
            download_manager.do('torrent_search')


            #### Torrent download ####

            # Don't actually download the torrents, create fake torrent files
            # based on the retreived torrent info
            def update_queued_torrents(self):
                for torrent in Torrent.objects.filter(status='Queued'):
                    # Mark directly as completed only if enough seeds
                    if torrent.seeds < 1:
                        torrent.status = 'Error'
                        torrent.save()
                    
                    torrent.status = 'Completed'
                    torrent.save()

                    # Iterate over each of the torrent files
                    for torrent_file_info in json.loads(torrent.file_list):
                        torrent_file = os.path.join(settings.TEST_DOWNLOAD_DIR, torrent_file_info['path'])
                        mkdir_p(os.path.split(torrent_file)[0])
                        
                        # Fill the files with fake data, to keep file sizes poportional
                        with open(torrent_file, 'w') as f: 
                            f.write('#' * (torrent_file_info['size']/1000)) 

            import wall.torrentdownloader
            default_update_queued_torrents = wall.torrentdownloader.TorrentDownloadManager.update_queued_torrents
            wall.torrentdownloader.TorrentDownloadManager.update_queued_torrents = update_queued_torrents

            # Caching of torrent info #

            def get_torrent_info_for_hash(self, hash):
                cached_content = get_cache(hash)
                if cached_content:
                    log.info('Torrent info found in cache for %s', hash)
                    return cached_content
                else:
                    torrent = default_get_torrent_info_for_hash(self, hash)
                    # Only cache once we've got the metadata
                    if torrent.has_metadata:
                        log.info('Adding torrent info in cache for %s', hash)
                        set_cache(hash, torrent)
                    return torrent
            
            default_get_torrent_info_for_hash = wall.torrentdownloader.Bittorrent.get_torrent_info_for_hash
            wall.torrentdownloader.Bittorrent.get_torrent_info_for_hash = get_torrent_info_for_hash

            def add_magnet(self, magnet_uri):
                hash = magnet_uri[20:60]
                if get_cache(hash) is None:
                    default_add_magnet(self, magnet_uri)
                else:
                    log.info('Not adding magnet, torrent info found in cache for %s', hash)

            default_add_magnet = wall.torrentdownloader.Bittorrent.add_magnet
            wall.torrentdownloader.Bittorrent.add_magnet = add_magnet

            def remove_hash(self, hash):
                if get_cache(hash) is None:
                    default_remove_hash(self, hash)
                else:
                    log.info('Not removing hash, torrent info found in cache for %s', hash)

            default_remove_hash = wall.torrentdownloader.Bittorrent.remove_hash
            wall.torrentdownloader.Bittorrent.remove_hash = remove_hash

            # Wait until all torrents metadata have been downloaded or cancelled #

            while Torrent.objects.filter(Q(status="New")|Q(status='Downloading metadata')|Q(status='Queued')).count() > 0:
                # The actual processing of the torrents objects
                download_manager.do('torrent_download')
                time.sleep(1)
            

            #### Package management ####

            download_manager.do('package_management')


            #### Video transcoding ####

            # Don't actually transcode anything
            vt = mock_video_transcoder.return_value

            # Never delay any transcoding processing
            vt.has_free_slot.return_value = True

            # Transcoding completes immediately
            vt.is_running.return_value = False

            # Run twice (first to start transcoding videos, second to mark transcoding as completed
            download_manager.do('video_transcoding')
            download_manager.do('video_transcoding')


            #### Report ####

            self.dump_test_db()
            self.dump_processing_stats()
            
        #### Cleanup ####

        except:
            raise
        finally:
            if default_open_url is not None:
                wall.helpers.open_url = default_open_url
            if default_get_url is not None:
                wall.helpers.get_url = default_get_url
            if default_update_queued_torrents is not None:
                wall.torrentdownloader.TorrentDownloadManager.update_queued_torrents = default_update_queued_torrents
            if default_get_torrent_info_for_hash is not None:
                wall.torrentdownloader.Bittorrent.get_torrent_info_for_hash = default_get_torrent_info_for_hash
            if default_add_magnet is not None:
                wall.torrentdownloader.Bittorrent.add_magnet = default_add_magnet
            if default_remove_hash is not None:
                wall.torrentdownloader.Bittorrent.remove_hash = default_remove_hash

    def dump_test_db(self):
        '''Writes the current DB state to a JSON file
        To be used with ./manage.py testserver <file> for later exploration'''

        from django.core import serializers

        all_objects = list(Series.objects.all()) \
                    + list(Season.objects.all()) \
                    + list(Episode.objects.all()) \
                    + list(Torrent.objects.all()) \
                    + list(Video.objects.all())

        with open(settings.TEST_DB_DUMP_PATH, "w") as f:
            data = serializers.serialize("json", all_objects, stream=f)

    def dump_processing_stats(self):
        '''Write down the status of objects currently loaded by tests in a HTML file'''

        c = self.client
        response = c.get('/status')

        mkdir_p(settings.COVERAGE_REPORT_HTML_OUTPUT_DIR)
        with open(os.path.join(settings.COVERAGE_REPORT_HTML_OUTPUT_DIR, "completion.html"), 'w') as f:
            f.write(response.content)


