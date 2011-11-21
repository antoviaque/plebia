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
import wall.helpers

import time, re, sys, urllib
import json


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


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
    
    plugin = active_plugins[0].get_plugin()
    log.debug("Selecting plugin %s for plugin point %s", plugin, plugin_point)

    return plugin

# TorrentSearcher ###################################################

class TorrentSearcher(PluginPoint):
    """
    Finds and builds the Torrent object for a given episode or season

    Must expose the following method:

        def search_torrent_by_string(self, name, episode_search_string):
            '''Search engine for an entry matching "<name>" AND "<episode_search_string>"'''

            return Torrent or None
    """
    
    def search_torrent_by_string(self, name, episode_search_string):
        pass
    
    def search_torrent(self, episode):
        '''Find a torrent for the provided episode, returns the Torrent object'''

        season = episode.season
        series = season.series

        episode_torrent = self.search_episode_torrent(episode)
        season_torrent = self.search_season_torrent(season)
        
        # When the series has only one season, also try without the season number
        if season_torrent is None and episode_torrent is None:
            series_torrent = self.search_series_torrent(series)
        else:
            series_torrent = None

        ## See what we should prefer ##

        if season_torrent is None and episode_torrent is None and series_torrent is None:
            torrent = Torrent()
            torrent.status = 'Error'
        
        # See if we should prefer the season or the episode
        elif season_torrent is not None or episode_torrent is not None:
            if season_torrent is None \
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

        # Only the series name alone
        else:
            torrent = series_torrent
            torrent.type = 'season'

        log.info('Selecting torrent %s', torrent)

        try:
            # Check if this torrent is already in the database
            existing_torrent = Torrent.objects.get(hash=torrent.hash)
            torrent = existing_torrent

            # Retreive tracker list
            tracker_url_list = self.get_tracker_list_for_torrent(torrent)
            if tracker_url_list:
                torrent.tracker_url_list = json.dumps(tracker_url_list)
        except Torrent.DoesNotExist:
            pass

        torrent.save()
        return torrent

    def get_tracker_list_for_torrent(self, torrent):
        '''To define in plugins for which getting the trackers list is
        an expensive operation - will only be called once we are sure
        we'll be using a given torrent from the results.
        
        Should return a list of trackers (python object)'''''

        pass

    def search_episode_torrent(self, episode):
        season = episode.season
        series = season.series
        episode_search_string = "s%02de%02d" % (season.number, episode.number)
        episode_torrent = self.search_torrent_by_string(self.clean_name(series.name), episode_search_string)
    
        log.info("Episode lookup for '%s' gave torrent %s", episode_search_string, episode_torrent)

        return episode_torrent

    def search_season_torrent(self, season):
        series = season.series

        for season_search_string in ["season %d" % season.number, \
                                      self.int_to_fullstring('season %s' % season.number)]:
            season_torrent = self.search_torrent_by_string(self.clean_name(series.name), season_search_string)

            log.info("Season lookup for '%s' gave torrent %s", season_search_string, season_torrent)

            if season_torrent is not None:
                break

        return season_torrent

    def search_series_torrent(self, series):
        series_search_string = self.clean_name(series.name)
        series_torrent = self.search_torrent_by_string(series_search_string, None)

        log.info("Series lookup for '%s' gave torrent %s", series_search_string, series_torrent)

        return series_torrent

    def clean_name(self, name):
        '''Remove unwanted characters from name'''

        clean_name = re.sub(r'[\W_]+', ' ', name).strip()
        log.debug("Clean name for '%s' is '%s'", name, clean_name)

        return clean_name

    def int_to_fullstring(self, text):
        '''Replaces all occurences of a 0-20 number as an int in a string, by its full letters counterpart. Ie "Season 2" becomes "Season two"'''

        int_dict = {0: 'zero', 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", \
                11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", \
                19: "nineteen", 20: "twenty"}

        text_full = text
        for num_int, num_text in int_dict.items():
            text = re.sub(r'\b%d\b' % num_int, num_text, text)

        log.debug("Fullstring translation of '%s' is '%s'", text, text_full)

        return text
       

class TorrentzSearcher(TorrentSearcher):
    name = 'torrentz-searcher'
    title = 'Torrentz Torrent Searcher'

    def search_torrent_by_string(self, name, episode_search_string):
        import feedparser

        # Retreive data from torrentz Atom feed
        search_string = u'(tv|television) "%s"' % name
        if episode_search_string is not None:
            search_string += u' "%s"' % episode_search_string

        log.info("Torrentz search for '%s'", search_string)
        url = "https://torrentz.eu/feed?q=%s" % urllib.quote_plus(search_string)
        content = wall.helpers.get_url(url)

        if content is None:
            return None
        
        # Get the list of torrents results
        res = feedparser.parse(content)
        if not res.entries:
            log.info("No results found for %s", search_string)
            return None

        # Build the torrent object
        for element in res.entries:
            torrent = self.get_torrent_from_result(element)

            if torrent.hash is None or torrent.seeds is None or torrent.seeds <= 0:
                log.info("Discarded result for lack of seeds or hash: %s", element)
            else:
                return torrent

        log.info("No good result found for %s", search_string)
        return None

    def get_torrent_from_result(self, result):
        '''Converts a result from the current engine to a Torrent object'''

        torrent = Torrent()

        torrent.title = wall.helpers.sane_text(result.title)
        torrent.hash = self.get_result_description_item('hash', result.description)
        torrent.seeds = self.get_result_description_item('seeds', result.description)
        torrent.peers = self.get_result_description_item('peers', result.description)
        
        return torrent

    def get_tracker_list_for_torrent(self, torrent):
        '''Get the list of trackers associated with this torrent'''

        from lxml.html import soupparser
        from lxml.cssselect import CSSSelector

        log.info("Retreiving list of trackers from Torrentz for torrent '%s'", torrent)
        url = "https://torrentz.eu/%s" % torrent.hash
        content = wall.helpers.get_url(url)

        # Get the list of torrents results
        sane_text = wall.helpers.sane_text(content)
        try:
            root = soupparser.fromstring(sane_text)
        except:
            return None

        sel = CSSSelector(".trackers dl")
        element_list = sel(root)
        if element_list is None:
            return None
        
        tracker_list = list()
        for element in element_list:
            url = element.cssselect("dt")[0].text_content()
            if url.startswith('http'):
                tracker_list.append(url)

        log.info("Trackers found for torrent %s: %s", torrent, tracker_list)
        return tracker_list

    def get_result_description_item(self, name, description):
        '''Extract a single item from a torrentz RSS result description'''

        m = re.search(r'\b' + name + r': ([0-9a-z]+)\b', description, re.IGNORECASE)
        if m is None:
            log.info('Could not find %s in description "%s"', name, description)
            return None
        else:
            return wall.helpers.sane_text(m.group(1))


class IsoHuntSearcher(TorrentSearcher):
    name = 'isohunt-searcher'
    title = 'isoHunt Torrent Searcher'

    def search_torrent_by_string(self, name, episode_search_string):
        '''Search isoHunt for an entry matching "<name>" AND "<episode_search_string>"'''

        torrent = Torrent()

        if episode_search_string is not None:
            search_string = '"%s" "%s"' % (name, episode_search_string)
        else:
            search_string = '"%s"' % name

        log.info("isoHunt search for '%s'", search_string)
        url = "http://ca.isohunt.com/js/json.php?ihq=%s&start=0&rows=20&sort=seeds&iht=3" % urllib.quote_plus(search_string)
        content = wall.helpers.get_url(url)

        if content is None:
            return None
       
        try:
            answer = json.loads(content)
            log.debug("Loaded JSON '%s'", answer)
        except ValueError:
            log.warn("Could not load JSON from '%s'", content)
            return None

        try:
            if answer['total_results'] == 0:
                log.info("Empty result set")
                return None

            result_list = answer['items']['list']
            if len(result_list) < 1:
                log.error("Empty result set with wrong total_results value")
                return None

            # Series whose name contains the name of the series we are looking for
            similar_series = Series.objects.filter(name__contains=name).exclude(name=name)

            for result in result_list:
                # Cleanup torrent name
                result['title'] = re.sub(r'</?b>', '', result['title'])
                result['title'] = re.sub(r'[\W_]+', ' ', result['title'])

                # IsoHunt returns all results containing a file matching the results - we want to match the title
                for element in [name, episode_search_string]:
                    if element is not None:
                        title_match = re.search(r'\b'+element+r'\b', result['title'], re.IGNORECASE)
                        if title_match is None:
                            log.debug('Discarded result "%s" (seem unrelated)', result['title'])
                            break
                
                # Discard series containing the searched series name
                similar_match = False
                for series in similar_series:
                     similar_match = re.search(series.name, result['title'])
                     if similar_match:
                        log.debug('Discarded result "%s" (seem to be about series "%s")', result['title'], series.name)
                        break

                if title_match and not similar_match \
                        and result['Seeds'] != '' and result['Seeds'] >= 1 \
                        and result['leechers'] != '' and result['category'] == 'TV':
                    log.info("Accepted result '%s' (%s seeds) %s", result['title'], result['Seeds'], result['hash'])
                    torrent.hash = result['hash']
                    torrent.seeds = result['Seeds']
                    torrent.peers = result['leechers']
                    torrent.details_url = wall.helpers.sane_text(result['link'], length=500)
                    torrent.tracker_url_list = json.dumps(result['tracker_url'])
                    return torrent
        except KeyError:
            log.error("Wrong format result")
            return None

        return None


