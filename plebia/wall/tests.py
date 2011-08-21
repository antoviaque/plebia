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

from plebia.wall.management.commands import torrent_update
from plebia.wall.management.commands import video_update
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
            self.assertEqual(response.status_code, 410) # "Gone"
        else:
            api_dict = json.loads(response.content)
            # Check each value in the provided dictionary to ensure they match the ones from the API object
            for (key, value) in value_dict.items():
                self.assertEqual(api_dict[key], value)

    def run_cron_commands(self):
        torrent_update.torrent_update()
        video_update.video_update()


    def test_000_home(self):
        c = self.client
        response = c.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)

        # User should see one form + another one in templates
        self.assertContains(response, '<form action="/" method="post">', count=2)


    def test_add_post_new_episode(self):
        """Add a new episode to the stream (real search engine query, individual episode)"""

        c = self.client
        url = "/"
        form = "form"
        valid_data = {"name": "Pioneer One",
                      "season": 1,
                      "episode": 2}

        # Required fileds - name
        data = valid_data.copy()
        data["name"] = ""
        response = c.post(url, data)
        self.assertFormError(response, form, "name", "This field is required.")

        # Required fileds - season
        data = valid_data.copy()
        data["season"] = ""
        response = c.post(url, data)
        self.assertFormError(response, form, "season", "This field is required.")

        # season must be a number
        data["season"] = "not_a_number"
        response = c.post(url, data)
        self.assertFormError(response, form, "season", "Enter a whole number.")

        # Required fileds - season
        data = valid_data.copy()
        data["episode"] = ""
        response = c.post(url, data)
        self.assertFormError(response, form, "episode", "This field is required.")

        # season must be a number
        data["episode"] = "not_a_number"
        response = c.post(url, data)
        self.assertFormError(response, form, "episode", "Enter a whole number.")

        # Test successful creation and redirection.
        data = valid_data.copy()
        response = c.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check model objects through API
        self.api_check('seriesseasonepisode', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 1, 'torrent': None})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'episode'})
        self.api_check('video', 1, None)


    @patch('plebia.wall.torrentutils.submit_form')
    def test_add_post_season(self, mock_submit_form):
        """Add an episode by downloading a full season (first and second episode of the same season)"""

        # Part 1 - Add first episode of this season #################

        c = self.client
        url = "/"
        data = {"name": "Test",
                "season": 2,
                "episode": 4}
        
        # Fake the results from the search engine
        values = [
                """<div class="results"><dl>
                        <dt><a href="/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa">Test season 2</a></dt>
                        <dd><span class="s">2643 Mb</span> <span class="u">103</span> <span class="d">38</span></dd>
                   </dl></div>""",
                "Could not match your exact query"]
        # Return different values for the two calls to the search engine (first: episode, second: season)
        def side_effect(url, text):
            return values.pop()
        mock_submit_form.side_effect = side_effect
        
        # Submit & check state
        response = c.post(url, data, follow=True)
        self.api_check('seriesseasonepisode', 1, {'number': 4, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': ''})
        self.api_check('video', 1, None)

        # Part 2 - Add second episode of the same season ############
        
        url = "/"
        data = {"name": "Test",
                "season": 2,
                "episode": 8}
        
        # Submit & check state
        response = c.post(url, data, follow=True)
        self.api_check('seriesseasonepisode', 2, {'number': 8, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': ''})
        self.api_check('video', 1, None)

        # Part 3 - Start download ###################################

        self.run_cron_commands()
        
        # Check state
        self.api_check('seriesseasonepisode', 2, {'number': 8, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 0.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': ''})
        self.api_check('video', 1, None)

        # Fake started download
        torrent_name = 'Test_Season_2'
        deluge_output = """
Name: """ + torrent_name + """
ID: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
State: Downloading Down Speed: 361.0 KiB/s Up Speed: 10.0 KiB/s ETA: 8m 4s
Seeds: 25 (28) Peers: 4 (388) Availability: 29.01
Size: 4.4 MiB/175.0 MiB Ratio: 0.000
Seed time: 0 days 00:00:00 Active: 0 days 00:01:33
Tracker status: 
Progress: 2.50% [#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]"""
        torrent_update.get_deluge_output = Mock(return_value=deluge_output)

        self.run_cron_commands()

        # Check state
        self.api_check('seriesseasonepisode', 1, {'number': 4, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 2.50, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': torrent_name, 'download_speed': '361.0 KiB/s', 'upload_speed': '10.0 KiB/s', 'eta': '8m 4s'})
        self.api_check('video', 1, None)

        # Part 4 - Complete download, start transcoding #############

        # Cleanup & set test download directory
        shutil.rmtree(settings.TEST_DOWNLOAD_DIR, ignore_errors=True)
        os.mkdir(settings.TEST_DOWNLOAD_DIR)
        os.mkdir(os.path.join(settings.TEST_DOWNLOAD_DIR, torrent_name))
        # Create season dir, with each of the two episodes contained in its own folder
        settings.DOWNLOAD_DIR = settings.TEST_DOWNLOAD_DIR
        season_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, torrent_name)
        episode_dir1 = os.path.join(season_dir, 's02e04')
        episode_dir2 = os.path.join(season_dir, 's02e08')
        os.mkdir(episode_dir1)
        os.mkdir(episode_dir2)
        # Fake downloaded files
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(episode_dir1, 'test1.avi'))
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(episode_dir2, 'test2.avi'))

        deluge_output = """
Name: """ + torrent_name + """
ID: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
State: Seeding Up Speed: 0.9 KiB/s
Seeds: 0 (1920) Peers: 3 (2066) Availability: 0.00
Size: 176.0 MiB/176.0 MiB Ratio: 5.196
Seed time: 0 days 16:02:37 Active: 0 days 16:06:40
Tracker status: """
        torrent_update.get_deluge_output = Mock(return_value=deluge_output)

        self.run_cron_commands()

        # Check state
        self.api_check('seriesseasonepisode', 1, {'number': 4, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': '/api/v1/video/1/'})
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'Completed', 'progress': 100.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': torrent_name})
        self.api_check('video', 1, {'status': 'Transcoding', \
                'original_path': os.path.join(torrent_name, 's02e04', 'test1.avi'), \
                'webm_path': os.path.join(torrent_name, 's02e04', 'test1.webm'), \
                'mp4_path': os.path.join(torrent_name, 's02e04', 'test1.mp4'), \
                'ogv_path': os.path.join(torrent_name, 's02e04', 'test1.ogv'), \
                'image_path': os.path.join(torrent_name, 's02e04', 'test1.jpg'), \
        })
        self.api_check('video', 2, {'status': 'Transcoding', \
                'original_path': os.path.join(torrent_name, 's02e08', 'test2.avi'), \
                'webm_path': os.path.join(torrent_name, 's02e08', 'test2.webm'), \
                'mp4_path': os.path.join(torrent_name, 's02e08', 'test2.mp4'), \
                'ogv_path': os.path.join(torrent_name, 's02e08', 'test2.ogv'), \
                'image_path': os.path.join(torrent_name, 's02e08', 'test2.jpg'), \
        })

        # Part 5 - Video status update ##############################

        self.run_cron_commands()

        # Check that the video is still transcoding
        self.api_check('video', 1, {'status': 'Transcoding'})
        self.api_check('video', 2, {'status': 'Transcoding'})



    def create_fake_season(self, name="Test"):
        series = Series.objects.get_or_create(name=name)[0]
        season = SeriesSeason.objects.get_or_create(number=2, series=series)[0]
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


    def test_video_not_found_in_torrent(self):
        """When a season torrent is successfully downloaded, but the video for this episode can't be found"""

        # Fake episode & post
        name = 'Test episode not found in season'
        episode = SeriesSeasonEpisode(number=10)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name)
        episode.save()
        post = Post(episode=episode).save()

        # Go to 'Completed mode to trigger episode search within torrent downloaded files
        episode.torrent.status = 'Completed'
        episode.torrent.save()

        # Directory is empty so video should be marked as not found
        self.api_check('video', 1, {'status': 'Not found'})


    @patch('plebia.wall.torrentutils.submit_form')
    def test_select_season_over_episode_when_few_seeds(self, mock_submit_form):
        """When an episode torrent is found but has only a few seeds, prefer the season"""

        c = self.client
        url = "/"
        data = {"name": "Test2",
                "season": 2,
                "episode": 4}
        
        # Fake the results from the search engine
        values = [
                """<div class="results"><dl>
                        <dt><a href="/cccccccccccccccccccccccccccccccccccccccc">Test2 season 2</a></dt>
                        <dd><span class="s">1000 Mb</span> <span class="u">103</span> <span class="d">38</span></dd>
                   </dl></div>""",
                """<div class="results"><dl>
                        <dt><a href="/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb">Test2 s02e04</a></dt>
                        <dd><span class="s">2643 Mb</span> <span class="u">3</span> <span class="d">4</span></dd>
                   </dl></div>"""]
        # Return different values for the two calls to the search engine (first: episode, second: season)
        def side_effect(url, text):
            return values.pop()
        mock_submit_form.side_effect = side_effect
        
        # Submit & check state
        response = c.post(url, data, follow=True)
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'hash': 'cccccccccccccccccccccccccccccccccccccccc', 'name': '', 'type': 'season'})


    def test_find_video_in_multiple_seasons_torrent(self):
        """Support multiple seasons torrent - Register all included seasons & find video"""

        # Fake episode
        name = 'Test multiple seasons'
        episode = SeriesSeasonEpisode(number=10)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="season")
        episode.save()

        # Build directory with multiple folders, one for each season
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, episode.torrent.name)
        os.mkdir(os.path.join(torrent_dir, 'Season 1'))
        os.mkdir(os.path.join(torrent_dir, 'SeaSon2'))
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, 'SeaSon2', 'S02E10.avi'))
        os.mkdir(os.path.join(torrent_dir, 'S3'))
        os.mkdir(os.path.join(torrent_dir, 's04'))

        # Go to Completed to trigger season & episode search within torrent downloaded files
        episode.torrent.status = 'Completed'
        episode.torrent.save()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, 'SeaSon2', 'S02E10.avi') })

        # Check that all seasons have been matched
        self.api_check('seriesseason', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('seriesseason', 2, {'number': 1, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('seriesseason', 3, {'number': 3, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('seriesseason', 4, {'number': 4, 'torrent': '/api/v1/torrent/1/'})
        
    
    def _test_find_single_episode_in_season_torrent(self, name, number, filename):
        """Helper method, to test finding a single episode name inside a season torrent
        The episode 'number' argument should be 1 on first call within same test method, and increase by 1 each call"""

        # Fake episode
        episode = SeriesSeasonEpisode(number=number)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="season")
        episode.save()

        # Copy test file to episode name to test
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, episode.torrent.name)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, filename))

        # Go to Completed to trigger season & episode search within torrent downloaded files
        episode.torrent.status = 'Completed'
        episode.torrent.save()

        # Check that the season/episode/video was found
        self.api_check('video', number, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, filename) })


    def create_fake_video(self, name, video_filename):
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, name)
        shutil.copy2(settings.TEST_VIDEO_PATH, os.path.join(torrent_dir, video_filename))

    def test_find_episodes_in_season_torrent(self):
        """Match episodes against their number inside a season torrent"""

        name = 'Test find episode in season'
        shutil.rmtree(settings.TEST_DOWNLOAD_DIR, ignore_errors=True)

        self._test_find_single_episode_in_season_torrent(name, 1, 's02e01.avi')
        self.create_fake_video(name, 'S02E20.avi') # Create potential false positive
        self._test_find_single_episode_in_season_torrent(name, 2, 'S02E02.avi')
        self._test_find_single_episode_in_season_torrent(name, 3, 's2e3.avi')
        self._test_find_single_episode_in_season_torrent(name, 4, '204.avi')
        self._test_find_single_episode_in_season_torrent(name, 5, '0205.avi')
        self._test_find_single_episode_in_season_torrent(name, 6, 'Season 2 - Episode 6.avi')
        self._test_find_single_episode_in_season_torrent(name, 7, 'season 02 episode 07.avi')


    def test_find_single_episode_in_season_torrent_subfolder(self):
        """When a season torrent has one season, but all its episodes contained in a subfolder"""

        # Fake episode
        name = 'Test episode name within season torrent subfolder'
        filename = 'Test - 201 - Title.avi'
        episode = SeriesSeasonEpisode(number=1)
        episode.season = self.create_fake_season(name=name)
        episode.torrent = self.create_fake_torrent(name=name, type="season")
        episode.save()

        # Copy test file to episode name to test
        torrent_dir = os.path.join(settings.TEST_DOWNLOAD_DIR, episode.torrent.name, 'sub folder')
        os.mkdir(torrent_dir)
        shutil.copy2(settings.TEST_VIDEO_PATH,os.path.join(torrent_dir, filename))

        # Go to Completed to trigger season & episode search within torrent downloaded files
        episode.torrent.status = 'Completed'
        episode.torrent.save()

        # Check that the season/episode/video was found
        self.api_check('video', 1, { 'status': 'New', 'original_path': os.path.join(episode.torrent.name, 'sub folder', filename) })




