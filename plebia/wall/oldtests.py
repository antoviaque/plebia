    def test_transcoding(self):
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

        self.run_cron_commands()

        # Check state
        self.api_check('episode', 1, {'number': 4, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/season/1/', 'video': '/api/v1/video/1/'})
        self.api_check('season', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'Completed', 'progress': 100.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': torrent_name})
        self.api_check('video', 1, {'status': 'Transcoding', \
                'original_path': os.path.join(torrent_name, 's02e04', 'test1.avi'), \
                'webm_path': os.path.join(torrent_name, 's02e04', 'test1.webm'), \
                'mp4_path': os.path.join(torrent_name, 's02e04', 'test1.mp4'), \
                'ogv_path': os.path.join(torrent_name, 's02e04', 'test1.ogv'), \
                'image_path': os.path.join(torrent_name, 's02e04', 'test1.jpg'), \
        })
        self.api_check('video', 3, {'status': 'Transcoding', \
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
        self.api_check('video', 3, {'status': 'Transcoding'})

    @patch('plebia.wall.torrentutils.submit_form')
    def test_add_post_series(self, mock_submit_form):
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
        self.api_check('episode', 1, {'number': 4, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/season/1/', 'video': None})
        self.api_check('season', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': ''})
        self.api_check('video', 1, None)

        # Part 2 - Add second episode of the same season ############
        
        url = "/"
        data = {"name": "Test",
                "season": 2,
                "episode": 8}
        
        # Submit & check state
        response = c.post(url, data, follow=True)
        self.api_check('episode', 3, {'number': 8, 'torrent': '/api/v1/torrent/1/', 'season': '/api/v1/season/1/', 'video': None})
        self.api_check('season', 1, {'number': 2, 'torrent': '/api/v1/torrent/1/'})
        self.api_check('torrent', 1, {'status': 'New', 'progress': 0.0, 'type': 'season', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'name': ''})
        self.api_check('video', 1, None)

    def test_add_post_new_series(self):
        """Add a post about a new series (search & add)"""

        c = self.client
        series_name = 'Pioneer One'
        url = "/ajax/search/%s" % series_name
        
        response = c.post(url)
        self.assertEqual(response.status_code, 200)

        # Check model objects through API
        self.api_check('episode', 1, {'number': 1, 'torrent': None, 'season': '/api/v1/season/1/', 'video': None})
        self.api_check('season', 1, {'number': 1, 'torrent': None})
        self.api_check('series', 1, {'name': series_name, 'torrent': None})
        self.api_check('torrent', 1, None)
        self.api_check('video', 1, None)


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

    



