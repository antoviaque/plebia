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

    def _test_find_single_episode_in_season_torrent(self, name, number, filename):
        """Helper method, to test finding a single episode name inside a season torrent
        The episode 'number' argument should be 1 on first call within same test method, and increase by 1 each call"""

        # Fake episode
        episode = Episode(number=number, tvdb_id=number)
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
        name = 'Test find episode in season'
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        os.mkdir(torrent_dir)

        self._test_find_single_episode_in_season_torrent(name, 1, 's02e01.avi')
        self.create_fake_video(name, 'S02E20.avi') # Create potential false positive
        self._test_find_single_episode_in_season_torrent(name, 2, 'S02E02.avi')
        self._test_find_single_episode_in_season_torrent(name, 3, 's2e3.avi')
        self._test_find_single_episode_in_season_torrent(name, 4, '204.avi')
        self._test_find_single_episode_in_season_torrent(name, 5, '0205.avi')
        self._test_find_single_episode_in_season_torrent(name, 6, 'Season 2 - Episode 6.avi')
        self._test_find_single_episode_in_season_torrent(name, 7, 'season 02 episode 07.avi')
        self._test_find_single_episode_in_season_torrent(name, 8, '02x08.avi')

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





