# -*- coding: utf-8 -*-
"""
thetvdb.com Python API
(c) 2009 James Smith (http://loopj.com)
(c) 2011 Xavier Antoviaque <xavier@antoviaque.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib
import datetime
import re

import xml.etree.cElementTree as ET

import wall.helpers

# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


class TheTVDB(object):
    def __init__(self, api_key):
        self.api_key = api_key
        self.mirror_url = "http://www.thetvdb.com"
        self.base_url =  self.mirror_url + "/api"
        self.base_key_url = "%s/%s" % (self.base_url, self.api_key)
        
    class Show(object):
        """A python object representing a thetvdb.com show record."""
        def __init__(self, node, mirror_url):
            # Main show details
            self.id = node.findtext("id")
            self.name = node.findtext("SeriesName")
            self.overview = node.findtext("Overview")
            # XXX Removed to allow the class to use the short description returned by show search to create Show() objects
            #self.genre = [g for g in node.findtext("Genre").split("|") if g]
            #self.actors = [a for a in node.findtext("Actors").split("|") if a]
            self.network = node.findtext("Network")
            self.content_rating = node.findtext("ContentRating")
            self.rating = node.findtext("Rating")
            if not self.rating:
                self.rating = None
            self.runtime = node.findtext("Runtime")
            self.status = node.findtext("Status")
            self.language = node.findtext("Language")
            if self.language is None:
                self.language = node.findtext("language")
        
            # Air details
            self.first_aired = TheTVDB.convert_date(node.findtext("FirstAired"))
            self.airs_day = node.findtext("Airs_DayOfWeek")
            self.airs_time = TheTVDB.convert_time(node.findtext("Airs_Time"))
        
            # Main show artwork
            self.banner_url = node.findtext("banner")
            self.poster_url = node.findtext("poster")
            self.fanart_url = node.findtext("fanart")

            # External references
            self.imdb_id = node.findtext("IMDB_ID")
            self.tvcom_id = node.findtext("SeriesID")
            if not self.tvcom_id:
                self.tvcom_id = None
            self.zap2it_id = node.findtext("zap2it_id")

            # When this show was last updated
            last_updated = node.findtext("lastupdated")
            if last_updated:
                self.last_updated = datetime.datetime.fromtimestamp(int(last_updated))
            else:
                self.last_updated = last_updated
        
        def __str__(self):
            import pprint
            return pprint.saferepr(self)

    class Episode(object):
        """A python object representing a thetvdb.com episode record."""
        def __init__(self, node, mirror_url):
            self.id = node.findtext("id")
            self.show_id = node.findtext("seriesid")
            self.name = node.findtext("EpisodeName")
            self.overview = node.findtext("Overview")
            self.season_number = int(node.findtext("SeasonNumber"))
            self.episode_number = int(node.findtext("EpisodeNumber"))
            self.director = node.findtext("Director")
            self.guest_stars = node.findtext("GuestStars")
            self.language = node.findtext("Language")
            self.production_code = node.findtext("ProductionCode")
            self.rating = node.findtext("Rating")
            if not self.rating:
                self.rating = None
            self.writer = node.findtext("Writer")

            # Air date
            self.first_aired = TheTVDB.convert_date(node.findtext("FirstAired"))
            
            # DVD Information
            self.dvd_chapter = node.findtext("DVD_chapter")
            self.dvd_disc_id = node.findtext("DVD_discid")
            self.dvd_episode_number = node.findtext("DVD_episodenumber")
            self.dvd_season = node.findtext("DVD_season")

            # Artwork/screenshot
            self.image = node.findtext("filename")

            # Episode ordering information (normally for specials)
            self.airs_after_season = node.findtext("airsafter_season")
            self.airs_before_season = node.findtext("airsbefore_season")
            self.airs_before_episode = node.findtext("airsbefore_episode")

            # Unknown
            self.combined_episode_number = node.findtext("combined_episode_number")
            self.combined_season = node.findtext("combined_season")
            self.absolute_number = node.findtext("absolute_number")
            self.season_id = node.findtext("seasonid")
            self.ep_img_flag = node.findtext("EpImgFlag")

            # External references
            self.imdb_id = node.findtext("IMDB_ID")

            # When this episode was last updated
            self.last_updated = datetime.datetime.fromtimestamp(int(node.findtext("lastupdated")))

        def __str__(self):
            return repr(self)

    @staticmethod
    def convert_time(time_string):
        """Convert a thetvdb time string into a datetime.time object."""

        if time_string is None:
            return None

        time_res = [re.compile(r"\D*(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?.*(?P<ampm>a|p)m.*", re.IGNORECASE), # 12 hour
                    re.compile(r"\D*(?P<hour>\d{1,2}):?(?P<minute>\d{2}).*")]                                     # 24 hour

        for r in time_res:
            m = r.match(time_string)
            if m:
                gd = m.groupdict()

                if "hour" in gd and "minute" in gd and gd["minute"] and "ampm" in gd:
                    hour = int(gd["hour"])
                    if gd["ampm"].lower() == "p":
                        hour += 12

                    return datetime.time(hour, int(gd["minute"]))
                elif "hour" in gd and "ampm" in gd:
                    hour = int(gd["hour"])
                    if gd["ampm"].lower() == "p":
                        hour += 12

                    return datetime.time(hour, 0)
                elif "hour" in gd and "minute" in gd:
                    return datetime.time(int(gd["hour"]), int(gd["minute"]))

        return None

    @staticmethod
    def convert_date(date_string):
        """Convert a thetvdb date string into a datetime.date object."""
        first_aired = None
        try:
            if date_string:
                first_aired = datetime.date(*map(int, date_string.split("-")))
        except ValueError:
            pass

        return first_aired

    def get_matching_shows(self, show_name):
        """Get a list of shows matching show_name."""
        get_args = urllib.urlencode({"seriesname": show_name}, doseq=True)
        url = "%s/GetSeries.php?%s" % (self.base_url, get_args)
        data = wall.helpers.open_url(url)
        show_list = []

        if data:
            try:
                tree = ET.parse(data)
                show_list = [TheTVDB.Show(show, self.mirror_url) for show in tree.getiterator("Series")]
            except SyntaxError:
                log.error("Could not parse contents of %s => %s", url, data.read())

        return show_list

    def get_show(self, show_id):
        """Get the show object matching this show_id."""
        url = "%s/series/%s/" % (self.base_key_url, show_id)
        data = wall.helpers.open_url(url)
        
        show = None
        try:
            tree = ET.parse(data)
            show_node = tree.find("Series")
        
            show = TheTVDB.Show(show_node, self.mirror_url)
        except SyntaxError:
            log.error("Could not parse contents of %s => %s", url, data.read())
        
        return show

    def get_episode(self, episode_id):
        """Get the episode object matching this episode_id."""
        url = "%s/episodes/%s/en.xml" % (self.base_key_url, episode_id)
        data = wall.helpers.open_url(url)
        
        tree = ET.parse(data)
        episode_node = tree.find("Episode")

        episode = TheTVDB.Episode(episode_node, self.mirror_url)
        
        return episode
    
    def get_show_and_episodes(self, show_id):
        """Get the show object and all matching episode objects for this show_id."""
        url = "%s/series/%s/all/" % (self.base_key_url, show_id)
        data = wall.helpers.open_url(url)
        
        show_and_episodes = None
        try:
            tree = ET.parse(data)
            show_node = tree.find("Series")
        
            show = TheTVDB.Show(show_node, self.mirror_url)
            episodes = []
        
            episode_nodes = tree.getiterator("Episode")
            for episode_node in episode_nodes:
                episodes.append(TheTVDB.Episode(episode_node, self.mirror_url))
        
            show_and_episodes = (show, episodes)
        except SyntaxError:
            log.error("Could not parse contents of %s => %s", url, data.read())
        
        return show_and_episodes

    def get_server_time(self):
        '''Get the current server time, used to generate update diffs'''
        url = "%s/Updates.php?type=none" % self.base_url
        data = wall.helpers.open_url(url)
        tree = ET.parse(data)
        timestamp = int(tree.findtext("Time"))

        return timestamp

    def get_updates_by_timestamp(self, timestamp):
        '''Returns (timestamp, series_list, episode_list) of updated series/episodes since <timestamp>'''
        url = "%s/Updates.php?type=all&time=%d" % (self.base_url, timestamp)
        data = wall.helpers.open_url(url)
        tree = ET.parse(data)

        series_node_list = tree.getiterator("Series")
        series_list = [x.text for x in series_node_list]

        episode_node_list = tree.getiterator("Episode")
        episode_list = [x.text for x in episode_node_list]

        timestamp = tree.findtext("Time")

        return (timestamp, series_list, episode_list)

    def get_updated_shows_by_period(self, period = "day"):
        """Get a list of show ids which have been updated within this period."""
        url = "%s/updates/updates_%s.xml" % (self.base_key_url, period)
        data = wall.helpers.open_url(url)
        tree = ET.parse(data)

        series_nodes = tree.getiterator("Series")

        return [x.findtext("id") for x in series_nodes]

    def get_updated_episodes_by_period(self, period = "day"):
        """Get a list of episode ids which have been updated within this period."""
        url = "%s/updates/updates_%s.xml" % (self.base_key_url, period)
        data = wall.helpers.open_url(url)
        tree = ET.parse(data)

        episode_nodes = tree.getiterator("Episode")

        return [(x.findtext("Series"), x.findtext("id")) for x in episode_nodes]

    def get_show_image_choices(self, show_id):
        """Get a list of image urls and types relating to this show."""
        url = "%s/series/%s/banners.xml" % (self.base_key_url, show_id)
        data = wall.helpers.open_url(url)
        tree = ET.parse(data)

        images = []

        banner_data = tree.find("Banners")
        banner_nodes = tree.getiterator("Banner")
        for banner in banner_nodes:
            banner_path = banner.findtext("BannerPath")
            banner_type = banner.findtext("BannerType")
            banner_url = "%s/banners/%s" % (self.mirror_url, banner_path)

            images.append((banner_url, banner_type))

        return images


