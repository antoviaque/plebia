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

from mock import Mock, patch
import json
import os, shutil


# Helpers ###########################################################




# Tests #############################################################

# TODO Test API along the way

class CardstoriesTest(TestCase):
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
        self.assertTrue('preload' in response.context)
        self.assertTrue('latest_post_list' in response.context)

        # We start with an empty db
        self.assertEqual(len(response.context['latest_post_list']), 0)

        # User should see one form
        self.assertContains(response, '<form action="/" method="post">', count=1)
        # and no post
        self.assertContains(response, '<p>No posts yet.</p>', count=1)


    def test_010_add_post_new_episode(self):
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

        # Check that the episode is correctly visible on the home page
        response = c.get("/")
        self.assertEqual(len(response.context['latest_post_list']), 1)
        self.assertContains(response, '<input type="hidden" name="episode_api_url" class="episode_api_url" value="/api/v1/seriesseasonepisode/1/" />', count=1)
        self.assertContains(response, '<input type="hidden" name="torrent_api_url" class="torrent_api_url" value="/api/v1/torrent/1/" />', count=1)
        self.assertContains(response, '<input type="hidden" name="video_api_url" class="video_api_url" value="" />', count=1)
        self.assertContains(response, 'Pioneer One - Season 1, Episode 2', count=1)

        # Check model objects through API
        self.api_check('seriesseasonepisode', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/seriesseason/1/', 'video': None})
        self.api_check('seriesseason', 1, {'number': 1, 'torrent': None})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'episode'})
        self.api_check('video', 1, None)


    @patch('plebia.wall.torrentutils.submit_form')
    def test_020_add_post_season(self, mock_submit_form):
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
        self.assertContains(response, 'Test - Season 2, Episode 4', count=1)
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
        self.assertContains(response, 'Test - Season 2, Episode 8', count=1)
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
State: Downloading Down Speed: 361.0 KiB/s Up Speed: 0.0 KiB/s ETA: 8m 4s
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
        self.api_check('torrent', 1, {'status': 'Downloading', 'progress': 2.50, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': torrent_name})
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

        # Get the home page & ajax video pages, to check that the videos are now displayed there
        response = c.get("/")
        self.assertEqual(len(response.context['latest_post_list']), 2)
        self.assertContains(response, '<source src="/static/stream.php?file_path=' + os.path.join(torrent_name, 's02e04', 'test1.webm') + "\" type='video/webm; codecs=\"vp8, vorbis\"' />", count=1)
        self.assertContains(response, '<source src="/static/stream.php?file_path=' + os.path.join(torrent_name, 's02e08', 'test2.webm') + "\" type='video/webm; codecs=\"vp8, vorbis\"' />", count=1)

        response = c.get("/ajax/video/1/")
        self.assertContains(response, '<source src="/static/stream.php?file_path=' + os.path.join(torrent_name, 's02e04', 'test1.webm') + "\" type='video/webm; codecs=\"vp8, vorbis\"' />", count=1)
        response = c.get("/ajax/video/2/")
        self.assertContains(response, '<source src="/static/stream.php?file_path=' + os.path.join(torrent_name, 's02e08', 'test2.webm') + "\" type='video/webm; codecs=\"vp8, vorbis\"' />", count=1)

        # Part 5 - Video status update ##############################

        self.run_cron_commands()

        # Check that the video is still transcoding
        self.api_check('video', 1, {'status': 'Transcoding'})
        self.api_check('video', 2, {'status': 'Transcoding'})





