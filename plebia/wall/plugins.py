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

from djangoplugins.point import PluginPoint
from wall.models import Torrent, Series
import time, re, sys

# Exceptions ########################################################

class NoActivePlugin(Exception):
    def __init__(self, plugin_point):
        self.plugin_point = plugin_point

    def __str__(self):
        return "Could not find an active plugin for %s" % repr(self.plugin_point)


# Helpers ###########################################################

def get_active_plugin(plugin_point):
    '''For a given PluginPoint, return the active plugin with the
    lowest order. NoActivePlugin exception is raised if no plugin is found'''

    active_plugins = plugin_point.get_plugins_qs()
    if len(active_plugins) < 1:
        raise NoActivePlugin(plugin_point)

    return active_plugins[0].get_plugin()


# TorrentSearcher ###################################################

class TorrentSearcher(PluginPoint):
    """
    Finds and builds the Torrent object for a given episode or season

    Must expose the following methods:

        def search_episode_torrent(self, episode):
            return Torrent or None
        def search_season_torrent(self, season):
            return Torrent or None
    """

    def search_torrent(self, episode):
        '''Find a torrent for the provided episode, returns the Torrent object'''

        # Do not spam the torrent search engine
        time.sleep(2)

        season = episode.season
        series = season.series

        episode_torrent = self.search_episode_torrent(episode)
        season_torrent = self.search_season_torrent(season)

        # See if we should prefer the season or the episode
        if season_torrent is None and episode_torrent is None:
            torrent = Torrent()
            torrent.status = 'Error'
        elif season_torrent is None \
                or (season_torrent.seeds < 10 and episode_torrent is not None):
            torrent = episode_torrent
            torrent.type = 'episode'
        elif episode_torrent is None \
                or episode_torrent.seeds < 10 \
                or episode_torrent.seeds*10 < season_torrent.seeds:
            torrent = season_torrent
            torrent.type = 'season'
        else:
            torrent = episode_torrent
            torrent.type = 'episode'

        print 'Chose %s' % torrent.hash

        torrent.save()
        return torrent


class IsoHuntSearcher(TorrentSearcher):
    name = 'isohunt-searcher'
    title = 'isoHunt Torrent Searcher'

    def search_episode_torrent(self, episode):
        season = episode.season
        series = season.series
        episode_search_string = "s%02de%02d" % (season.number, episode.number)
        episode_torrent = self.search_torrent_by_string(series.name, episode_search_string)

        return episode_torrent

    def search_season_torrent(self, season):
        series = season.series
        episode_search_string = "season %d" % season.number
        season_torrent = self.search_torrent_by_string(series.name, episode_search_string)

        return season_torrent

    def search_torrent_by_string(self, name, episode_search_string):
        '''Search isoHunt for an entry matching name" AND "<episode_search_string>"'''

        import urllib, json
        torrent = Torrent()

        search_string = '"%s" "%s"' % (name, episode_search_string)
        print "Request (isoHunt): '%s'" % search_string
        url = "http://ca.isohunt.com/js/json.php?ihq=%s&start=0&rows=20&sort=seeds&iht=3" % urllib.quote_plus(search_string)
        content = self.get_url(url)

        if content is None:
            return None
       
        try:
            answer = json.loads(content)
        except ValueError:
            return None

        try:
            result_list = answer['items']['list']
            if len(result_list) < 1:
                return None

            # Series whose name contains the name of the series we are looking for
            similar_series = Series.objects.filter(name__contains=name).exclude(name=name)

            for result in result_list:
                # Cleanup torrent name
                result['title'] = re.sub(r'</?b>', '', result['title'])
                result['title'] = re.sub(r'[\W_]+', ' ', result['title'])

                # IsoHunt returns all results containing a file matching the results - we want to match the title
                for element in [name, episode_search_string]:
                    title_match = re.search(r'\b'+element+r'\b', result['title'], re.IGNORECASE)
                    if title_match is None:
                        break
                
                # Discard series containing the searched series name
                similar_match = False
                for series in similar_series:
                     similar_match = re.search(series.name, result['title'])
                     if similar_match:
                        print 'Discarded series "%s" from "%s"' % (series.name, result['title'])
                        break

                if title_match and not similar_match \
                        and result['Seeds'] != '' and result['Seeds'] >= 1 \
                        and result['leechers'] != '' and result['category'] == 'TV':
                    print "Found '%s' (%s seeds) %s" % (result['title'], result['Seeds'], result['hash'])
                    torrent.hash = result['hash']
                    torrent.seeds = result['Seeds']
                    torrent.peers = result['leechers']
                    torrent.details_url = result['link']
                    return torrent
        except KeyError:
            print sys.exc_type, ":", "%s is not in the list." % sys.exc_value
            return None

        return None

    def get_url(self, url):
        '''Returns the content at the provided URL, None if error'''

        import requests
        r = requests.get(url)

        if r.status_code == requests.codes.ok:
            return r.content
        else:
            return None
       

# FIXME: Currently grabbing pages, in the absence of a proper API
#        Do not use as is.
#class TorrentzSearcher(TorrentSearcher):
#    name = 'torrentz-searcher'
#    title = 'Torrentz Torrent Searcher'
#
#    def search_episode_torrent(self, episode):
#        season = episode.season
#        search_string = "(tv|television) %s s%02de%02d" % (series.name, season.number, episode.number)
#        episode_torrent = self.search_torrent_by_string(search_string)
#
#        return episode_torrent
#
#    def search_season_torrent(self, season):
#        search_string = "(tv|television) %s season %d" % (series.name, season.number)
#        season_torrent = self.search_torrent_by_string(search_string)
#
#        return season_torrent
#
#    def search_torrent_by_string(self, search_string):
#        torrent = Torrent()
#        html_result = self.submit_form("http://torrentz.com/", search_string)
#
#        # First check if any torrent was found at all
#        if(html_result is None or re.search("Could not match your exact query", html_result)):
#            return None
#        
#        # Get the list of torrents results
#        sane_text = self.sanitize_text(html_result)
#        root = soupparser.fromstring(sane_text)
#        sel = CSSSelector(".results dl")
#        element = sel(root)
#        if element is None:
#            return None
#        else:
#            # Build the torrent object
#            torrent.hash = element[0].cssselect("dt a")[0].get("href")[1:]
#            torrent.seeds = int(element[0].cssselect("dd .u")[0].text_content().translate(None, ','))
#            torrent.peers = int(element[0].cssselect("dd .d")[0].text_content().translate(None, ','))
#            if torrent.hash is None or torrent.seeds is None or torrent.seeds <= 0:
#                return None
#            else:
#                return torrent
#
#
#    def submit_form(self, url, text):
#        import httplib
#
#        try:
#            br = mechanize.Browser()
#            br.open(url)
#
#            # Debug - show every request in log
#            curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
#            print '%s: %s => %s' % (curr_time, url, text)
#
#            br.select_form(nr=0)
#            br["f"] = text
#            response = br.submit()
#            html_result = response.get_data()
#        except httplib.BadStatusLine:
#            html_result = None
#
#        return html_result
#
#    def sanitize_text(self, text):
#        '''Remove non-string characters from text'''
#
#        sane_text = u''
#
#        # HTML NULL entity
#        text = text.replace('&#0', '')
#
#        for c in text:
#            # Make sure it's not a control character
#            if ord(c) >= 32 and ord(c) <= 126:
#                sane_text += c
#
#        return sane_text

