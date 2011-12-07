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
from wall.torrentmagic import TorrentMagic
import wall.helpers

import urllib


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
            '''Search engine for a list of results matching "<name>" AND "<episode_search_string>"'''

            return (Torrent, Torrent, ...) or None

    Can override the following method:

        def get_tracker_list_for_torrent(self, torrent):
            '''Get the list of trackers associated with this torrent
            Can be overridden by the plugin to define a custom method'''

            return ('http://...', 'http://...', ...)
    """
    
    def search_torrent_by_string(self, name, episode_search_string):
        '''Returns search results as a list of Torrent() objects,
        by decreasing number of seeds.
        Torrent() objects are not saved to not trigger download.'''

        pass

    def search_season_torrent_dict(self, series):
        '''For a given series, try to find season torrents for each of its seasons
        returns: {1: torrent_object, 2: torrent_object, etc.}
        Season number not found are not included in the returned dict'''

        # Run search engine query
        torrent_list = self.search_torrent_by_string(wall.helpers.normalize_text(series.name))

        nb_seasons = series.season_set.count()
        season_torrent_dict = dict()
        for torrent in torrent_list:
            torrent.type = 'season'

            # Stop processing the list when we reach low seeds torrent results
            if torrent.seeds < 1:
                log.info('No seed on torrent "%s", stopping', torrent)
                break

            # Make assumptions about the content of the torrent based on
            # the information we have gathered about it so far
            torrent_details = TorrentMagic(torrent, series_name=series.name)

            # Filter out unrelated or unusable results, and partial seasons
            if torrent_details.similar_series or \
                    torrent_details.iso or \
                    torrent_details.other_language or \
                    torrent_details.partial_season or \
                    torrent_details.unrelated_series:
                log.info('Bad result "%s", continuing', torrent)
                continue

            # Torrents that contain all seasons
            if torrent_details.complete_series:
                log.info('All seasons found in torrent "%s", stopping', torrent)
                for season in series.season_set.all():
                    # Check the season hasn't been added yet
                    if season.number not in season_torrent_dict:
                        season_torrent_dict[season.number] = torrent
                    else:
                        log.info('Season %d already found for torrent "%s"', season.number, torrent)
                
                # Keep this torrent
                torrent = self.update_torrent_with_tracker_list(torrent)
                torrent.save()

                # No need for more seasons
                break

            # Torrents that contain one or several seasons
            if len(torrent_details.season_number_list) >= 1:
                log.info('Seasons %s found in torrent "%s"', torrent_details.season_number_list, torrent)
                nb_season_used = 0
                for season_number in torrent_details.season_number_list:
                    # Make sure the season numbers exist & hasn't been found yet
                    if series.season_set.filter(number=season_number).count() == 1 and season_number not in season_torrent_dict:
                        season_torrent_dict[season_number] = torrent
                        nb_season_used += 1
                    else:
                        log.info('Season %d already found for torrent "%s"', season_number, torrent)

                # Keep this torrent only if we need it
                if nb_season_used >= 1:
                    torrent = self.update_torrent_with_tracker_list(torrent)
                    torrent.save()

                continue

            # Stop processing when we have all the seasons
            if len(season_torrent_dict) >= nb_seasons:
                log.info('Found all seasons for series "%s", stopping', series)
                break

        return season_torrent_dict

    def search_episode_torrent(self, episode):
        '''Find a torrent for the provided episode, returns the Torrent object'''

        season = episode.season
        series = season.series

        # Run search engine query
        search_string = "s%02de%02d" % (season.number, episode.number)
        torrent_list = self.search_torrent_by_string(wall.helpers.normalize_text(series.name), search_string)
        
        # Isolate the right torrent
        torrent = None
        for torrent_result in torrent_list:
            if torrent_result.hash is None or torrent_result.seeds is None or torrent_result.seeds <= 0:
                log.info("Discarded result for lack of seeds or hash: %s", torrent_result)
            else:
                torrent = torrent_result
                break

        log.info("Episode lookup for '%s' gave torrent %s", search_string, torrent)
        
        if torrent is None:
            torrent = Torrent()
            torrent.status = 'Error'
        
        try:
            # Check if this torrent is already in the database
            existing_torrent = Torrent.objects.get(hash=torrent.hash)
            torrent = existing_torrent
        except Torrent.DoesNotExist:
            torrent = self.update_torrent_with_tracker_list(torrent)

        torrent.save()
        return torrent

    def update_torrent_with_tracker_list(self, torrent):
        '''Get the tracker list for torrent, add it, and save torrent'''

        import json
        
        log.info("Retreiving list of trackers for torrent '%s'", torrent)
        tracker_url_list = self.get_tracker_list_for_torrent(torrent)
        if tracker_url_list:
            torrent.tracker_url_list = json.dumps(tracker_url_list)

        return torrent

    def get_tracker_list_for_torrent(self, torrent):
        '''Get the list of trackers associated with this torrent
        Can be overridden by the plugin to define a custom method'''

        url = "http://bitsnoop.com/api/trackers.php?hash=%s&json=1" % torrent.hash
        answer = wall.helpers.get_url_json(url)

        if answer is None or answer == "NOTFOUND":
            return None

        tracker_list = list()
        for element in answer:
            try:
                if element['ANNOUNCE'].startswith('http') and element['NUM_SEEDERS'] >= 1:
                    tracker_list.append(element['ANNOUNCE'])
            except exceptions.ValueError:
                continue

        log.info("Trackers found for torrent %s: %s", torrent, tracker_list)
        return tracker_list


class TorrentzSearcher(TorrentSearcher):
    name = 'torrentz-searcher'
    title = 'Torrentz Torrent Searcher'

    def search_torrent_by_string(self, name, episode_search_string=None):
        # Retreive data from torrentz Atom feed
        search_string = u'(tv|television) "%s"' % name
        if episode_search_string is not None:
            search_string += u' "%s"' % episode_search_string

        log.info("Torrentz search for '%s'", search_string)
        url = "http://torrentz.eu/feed?q=%s" % urllib.quote_plus(search_string)
        entries = wall.helpers.get_url_rss(url)

        if entries is None:
            return list()
        
        # Build the torrent objects list
        torrent_list = list()
        for element in entries:
            torrent = self.get_torrent_from_result(element)
            torrent_list.append(torrent)

        return torrent_list

    def get_torrent_from_result(self, result):
        '''Converts a result from the current engine to a Torrent object'''

        torrent = Torrent()

        torrent.name = wall.helpers.sane_text(result.title)
        torrent.hash = self.get_result_description_item('hash', result.description)
        torrent.seeds = self.get_result_description_item('seeds', result.description)
        torrent.peers = self.get_result_description_item('peers', result.description)
        
        return torrent

    def get_result_description_item(self, name, description):
        '''Extract a single item from a torrentz RSS result description'''

        import re

        m = re.search(r'\b' + name + r': ([0-9a-z]+)\b', description, re.IGNORECASE)
        if m is None:
            log.info('Could not find %s in description "%s"', name, description)
            return None
        else:
            return wall.helpers.sane_text(m.group(1))


# class IsoHuntSearcher(TorrentSearcher):
#     name = 'isohunt-searcher'
#     title = 'isoHunt Torrent Searcher'
# 
#     def search_torrent_by_string(self, name, episode_search_string):
#         '''Search isoHunt for an entry matching "<name>" AND "<episode_search_string>"'''
# 
#         torrent = Torrent()
# 
#         if episode_search_string is not None:
#             search_string = '"%s" "%s"' % (name, episode_search_string)
#         else:
#             search_string = '"%s"' % name
# 
#         log.info("isoHunt search for '%s'", search_string)
#         url = "http://ca.isohunt.com/js/json.php?ihq=%s&start=0&rows=20&sort=seeds&iht=3" % urllib.quote_plus(search_string)
#         answer = wall.helpers.get_url_json(url)
#         if answer is None:
#             return None
#
#         try:
#             if answer['total_results'] == 0:
#                 log.info("Empty result set")
#                 return None
# 
#             result_list = answer['items']['list']
#             if len(result_list) < 1:
#                 log.error("Empty result set with wrong total_results value")
#                 return None
# 
#             for result in result_list:
#                 # Cleanup torrent name
#                 result['title'] = re.sub(r'</?b>', '', result['title'])
#                 result['title'] = re.sub(r'[\W_]+', ' ', result['title'])
# 
#                 # IsoHunt returns all results containing a file matching the results - we want to match the title
#                 for element in [name, episode_search_string]:
#                     if element is not None:
#                         title_match = re.search(r'\b'+element+r'\b', result['title'], re.IGNORECASE)
#                         if title_match is None:
#                             log.debug('Discarded result "%s" (seem unrelated)', result['title'])
#                             break
#                 
#                 if title_match and not similar_match \
#                         and result['Seeds'] != '' and result['Seeds'] >= 1 \
#                         and result['leechers'] != '' and result['category'] == 'TV':
#                     log.info("Accepted result '%s' (%s seeds) %s", result['title'], result['Seeds'], result['hash'])
#                     torrent.hash = result['hash']
#                     torrent.seeds = result['Seeds']
#                     torrent.peers = result['leechers']
#                     torrent.details_url = wall.helpers.sane_text(result['link'], length=500)
#                     torrent.tracker_url_list = json.dumps(list(result['tracker_url']))
#                     return torrent
#         except KeyError:
#             log.error("Wrong format result")
#             return None
# 
#         return None


