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

from plebia.wall.models import *
from plebia.wall.torrentdownloader import TorrentDownloader
from plebia.wall.plugins import IsoHuntSearcher, TorrentSearcher

from mock import Mock, patch
import json
import os, shutil


# Helpers ###########################################################

import os, errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise


# Tests #############################################################

# TODO Test API along the way

class PlebiaTest(TestCase):
    #fixtures = ['video.json']

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

        # Create torrent directory
        mkdir_p(settings.TEST_DOWNLOAD_DIR)
        mkdir_p(os.path.join(settings.TEST_DOWNLOAD_DIR, torrent.name))
        settings.DOWNLOAD_DIR = settings.TEST_DOWNLOAD_DIR

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
        self.create_fake_video(name, u'S02E20.avi') # Create potential false positives
        self.create_fake_video(name, u's2e20.avi')
        self._test_find_single_episode_in_season_torrent(name, 2, u'S02E02.avi')
        self._test_find_single_episode_in_season_torrent(name, 3, u's2e3.avi')
        self._test_find_single_episode_in_season_torrent(name, 4, u'204.avi')
        self._test_find_single_episode_in_season_torrent(name, 5, u'0205.avi')
        self._test_find_single_episode_in_season_torrent(name, 6, u'Season 2 - Episode 6.avi')
        self._test_find_single_episode_in_season_torrent(name, 7, u'season 02 episode 07.avi')
        self._test_find_single_episode_in_season_torrent(name, 8, u'02x08.avi')
        self._test_find_single_episode_in_season_torrent(name, 9, u'[2.09].avi')
        self._test_find_single_episode_in_season_torrent(name, 10, u'[2x10].avi')
        self._test_find_single_episode_in_season_torrent(name, 11, u's02e11.m4v') # Unknown on some mime.types files
        self._test_find_single_episode_in_season_torrent(name, 12, u'Test 2-12.avi')
        self._test_find_single_episode_in_season_torrent(name, 13, u'Test s02 e13.avi')
        self._test_find_single_episode_in_season_torrent(name, 14, u'Test (2x14 Test) test.avi')
        self._test_find_single_episode_in_season_torrent(name, 15, u'Test (2x15 Test) testó.avi') # Unicode
        self._test_find_single_episode_in_season_torrent(name, 16, u'episode.with-only_title.avi', episode_name='Episode with only title')
        self._test_find_single_episode_in_season_torrent(name, 17, u'Test - S2 E17 - Episode.avi')

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

    @patch.object(TorrentDownloader, 'get_deluge_output')
    @patch.object(TorrentDownloader, 'cancel_hash')
    def update_torrent_from_deluge_output(self, deluge_output, torrent, mock_cancel_hash, mock_get_deluge_output, cancel_hash=False):
        '''Mock TorrentDownloader.get_deluge_output to pass the provided fake deluge_output and update the torrent with it'''

        mock_get_deluge_output.return_value = deluge_output

        torrent_downloader = TorrentDownloader()
        torrent_downloader.update_torrent_list()
        torrent_downloader.update_no_seed_timeout()

        updated_torrent = torrent_downloader.get_torrent_by_hash(torrent.hash)
        torrent.update_from_torrent(updated_torrent)

        # If requested check that the cancel_hash() method was called
        if cancel_hash:
            mock_cancel_hash.assert_called_once_with(torrent.hash)

    def test_torrent_download_update_queued(self):
        '''Updates info about a queued torrent download from torrent downloader'''

        # Init data
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_hash + """
ID: """ + torrent_hash + """
State: Queued
Seeds: 0 (0) Peers: 0 (0) Availability: 0.00
Size: 0.0 KiB/0.0 KiB Ratio: -1.000
Seed time: 0 days 00:00:00 Active: 0 days 00:00:01
Tracker status: 
Progress: 0.00% [~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]"""

        self.update_torrent_from_deluge_output(deluge_output, torrent)

        # Check state
        self.api_check('torrent', 1, {'status': 'Queued', 'progress': 0.0, 'type': 'season', 'hash': torrent_hash, 'name': '', 'download_speed': '0.0 KiB/s', 'upload_speed': '0.0 KiB/s', 'eta': '', 'active_time': '0 days 00:00:01', 'seeds': 0, 'peers': 0})


    def test_torrent_download_update_started_no_progress(self):
        '''Updates info about a torrent download from torrent downloader, when just started but not reached any seeds/peers yet'''

        # Init data
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_hash + """
ID: """ + torrent_hash + """
State: Downloading Down Speed: 0.0 KiB/s Up Speed: 0.0 KiB/s
Seeds: 0 (0) Peers: 0 (0) Availability: 0.00
Size: 0.0 KiB/0.0 KiB Ratio: -1.000
Seed time: 0 days 00:00:00 Active: 0 days 00:21:10
Tracker status: 
Progress: 0.00% [~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]"""

        self.update_torrent_from_deluge_output(deluge_output, torrent)

        # Check state
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 0.0, 'type': 'season', 'hash': torrent_hash, 'name': '', 'download_speed': '0.0 KiB/s', 'upload_speed': '0.0 KiB/s', 'eta': '', 'active_time': '0 days 00:21:10', 'seeds': 0, 'peers': 0})

    def test_torrent_download_update_no_seed_timeout(self):
        '''Updates info about a torrent download from torrent downloader, when the download has been started for some time and has no seed'''

        # Init data
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_hash + """
ID: """ + torrent_hash + """
State: Downloading Down Speed: 0.0 KiB/s Up Speed: 0.0 KiB/s
Seeds: 0 (0) Peers: 1 (2) Availability: 0.00
Size: 50.0 KiB/100.0 KiB Ratio: -1.000
Seed time: 0 days 00:00:00 Active: 0 days 10:21:10
Tracker status: 
Progress: 50.00% [##############################~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]"""

        self.update_torrent_from_deluge_output(deluge_output, torrent, cancel_hash=True)

        # Check state
        self.api_check('torrent', 1, {'status': 'Error', 'progress': 50.0, 'type': 'season', 'hash': torrent_hash, 'name': '', 'download_speed': '0.0 KiB/s', 'upload_speed': '0.0 KiB/s', 'eta': '', 'active_time': '0 days 10:21:10', 'seeds': 0, 'peers': 2})

    def test_torrent_download_update_started_progress(self):
        '''Updates info about a torrent download from torrent downloader, when it has made some progress'''

        # Init data
        torrent_name = 'Test_Season_2'
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_name + """
ID: """ + torrent_hash + """
State: Downloading Down Speed: 361.0 KiB/s Up Speed: 10.0 KiB/s ETA: 8m 4s
Seeds: 25 (28) Peers: 4 (388) Availability: 29.01
Size: 4.4 MiB/175.0 MiB Ratio: 0.000
Seed time: 0 days 00:00:00 Active: 0 days 00:01:33
Tracker status: 
Progress: 2.50% [#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]"""

        self.update_torrent_from_deluge_output(deluge_output, torrent)

        # Check state
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 2.50, 'type': 'season', 'hash': torrent_hash, 'name': torrent_name, 'download_speed': '361.0 KiB/s', 'upload_speed': '10.0 KiB/s', 'eta': '8m 4s', 'active_time': '0 days 00:01:33', 'seeds': 28, 'peers': 388})

    def test_torrent_download_update_finishing(self):
        '''Updates info about a torrent download from torrent downloader, when it is in the last percent (marked as 100%)'''

        # Init data
        torrent_name = 'Test_Season_2'
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_name + """
ID: """ + torrent_hash + """
State: Downloading Down Speed: 361.0 KiB/s Up Speed: 10.0 KiB/s ETA: 8m 4s
Seeds: 25 (28) Peers: 4 (388) Availability: 29.01
Size: 174.4 MiB/175.0 MiB Ratio: 0.000
Seed time: 0 days 00:00:00 Active: 0 days 00:01:33
Tracker status: 
Progress: 100.00% [############################################################]"""

        self.update_torrent_from_deluge_output(deluge_output, torrent)

        # Check state
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 100.0, 'type': 'season', 'hash': torrent_hash, 'name': torrent_name, 'download_speed': '361.0 KiB/s', 'upload_speed': '10.0 KiB/s', 'eta': '8m 4s', 'active_time': '0 days 00:01:33', 'seeds': 28, 'peers': 388})

    def test_torrent_download_update_completed(self):
        '''Updates info about a torrent download from torrent downloader, when it completes'''

        # Init data
        torrent_name = 'Test_Season_2'
        torrent_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        torrent = Torrent(hash=torrent_hash, name='', type='season', status='Queued')
        torrent.save()

        deluge_output = """
Name: """ + torrent_name + """
ID: """ + torrent_hash + """
State: Seeding Up Speed: 0.9 KiB/s
Seeds: 0 (1920) Peers: 3 (2066) Availability: 0.00
Size: 176.0 MiB/176.0 MiB Ratio: 5.196
Seed time: 0 days 16:02:37 Active: 0 days 16:06:40
Tracker status: """

        self.update_torrent_from_deluge_output(deluge_output, torrent)

        # Check state
        self.api_check('torrent', 1, {'status': 'Completed', 'progress': 100.0, 'type': 'season', 'hash': torrent_hash, 'name': torrent_name, 'download_speed': '0.0 KiB/s', 'upload_speed': '0.9 KiB/s', 'eta': '', 'active_time': '0 days 16:06:40', 'seeds': 1920, 'peers': 2066})

    def build_isohunt_result(self, torrent_dict_array):
        """Builds and returns a IsoHunt result string. torrent_dict_array=[{'name':'Torrent name', 'hash':'aaaa', 'seeds':10, 'peers':20}, ...]"""

        result = u"""{"title": "","link": "http://isohunt.com","description": "BitTorrent Search","language": "en-us","category": "TV","max_results": 1000,"ttl": 15,"image": {"title": "","url": "http://isohunt.com/img/buttons/isohunt-02.gif","link": "http://isohunt.com/","width": 157,"height": 45}, "lastBuildDate": "Tue, 01 Nov 2011 12:01:51 GMT","pubDate": "Tue, 01 Nov 2011 12:01:51 GMT","total_results":2, "censored":0, "items": {"list": ["""

        for torrent_dict in torrent_dict_array:
            result += u"""{"title":"%s","link":"http:\/\/isohunt.com\/torrent_details","guid":"213882961","enclosure_url":"http://ca.isohunt.com/download/213882961/","length":379895939,"tracker":"tracker.openbittorrent.com","tracker_url":"http:\/\/tracker.openbittorrent.com:80\/announce","kws":"","exempts":"","category":"TV","original_site":"original.com","original_link":"http:\/\/original.com\/torrent","size":"362.3 MB","files":10,"Seeds":%d,"leechers":%d,"downloads":671,"votes":0,"comments":0,"hash":"%s","pubDate":"Sun, 04 Jul 2010 17:28:51 GMT"},""" % (torrent_dict['name'], torrent_dict['seeds'], torrent_dict['peers'], torrent_dict['hash'])

        result = result[:-1] # Remove trailing ','
        result += u"]}}" # Close

        return result

    @patch.object(IsoHuntSearcher, 'get_url')
    def run_isohunt_search(self, episode, episode_result, season_result, mock_get_url):
        '''Run plugin code for searching torrent, based on mock isoHunt results'''
        
        # Return different values for the two calls to the search engine (first: episode, second: season)
        values = [season_result, episode_result]
        def side_effect(url):
            return values.pop()
        mock_get_url.side_effect = side_effect
        
        searcher = IsoHuntSearcher()
        searcher.search_torrent(episode)

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
        name = 'Test series.'
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


