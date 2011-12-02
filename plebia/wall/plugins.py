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
        torrent_list = self.search_torrent_by_string(self.clean_name(series.name))

        nb_seasons = series.season_set.count()
        season_torrent_dict = dict()
        for torrent in torrent_list:
            torrent_name = self.clean_name(torrent.name)
            torrent.type = 'season'

            # Stop processing the list when we reach low seeds torrent results
            if torrent.seeds < 1:
                log.info('No seed on torrent "%s", stopping', torrent)
                break

            # Stop processing when we have all the seasons
            if len(season_torrent_dict) >= nb_seasons:
                log.info('Found all seasons for series "%s", stopping', series)
                break

            # Filter out unrelated or unusable results, and partial seasons
            if self.is_bad_result(torrent_name, series.name) or \
                    self.is_partial_season_result(torrent_name) or \
                    self.is_single_episode_result(torrent_name):
                log.info('Bad result "%s", continuing', torrent)
                continue

            # Torrents that contain one or several seasons
            season_number_list = self.get_season_number_list(torrent_name)
            if len(season_number_list) >= 1:
                log.info('Seasons %s found in torrent "%s"', season_number_list, torrent)
                nb_season_used = 0
                for season_number in season_number_list:
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

            # Torrents that contain all seasons
            if self.is_all_seasons_result(torrent_name):
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

        return season_torrent_dict

    def is_bad_result(self, torrent_name, series_name):
        '''Check if the torrent is obviously unrelated to series or unusuable
        Note that if False is returned it doesn't garantee that the torrent is actually a good
        match for this series, only a return value of True is meaningful'''

        # Series whose name contains the name of the series we are looking for
        similar_series_list = Series.objects.filter(name__contains=series_name).exclude(name=series_name)

        # Discard series containing the searched series name
        for similar_series in similar_series_list:
            similar_match = re.search(similar_series.name, torrent_name, re.IGNORECASE)
            if similar_match:
                log.info('Result "%s" seem to be about series "%s"', torrent_name, similar_series.name)
                return True

        # Discard results usually containing an ISO file
        if re.search(r"\b(disk|disc|iso)\b", torrent_name, re.IGNORECASE):
            log.info('Result "%s" seem to be an ISO', torrent_name)
            return True

        # Discard results in other languages
        if re.search(r"\b(ITA|NL|FR|FRENCH|DUTCH)\b", torrent_name, re.IGNORECASE):
            log.info('Result "%s" seem to be in another language', torrent_name)
            return True

        return False

    def is_partial_season_result(self, torrent_name):
        '''Check if the torrent does not contain a whole season'''

        if re.search(r"\b(Ep|Episodes?) *[0-9]+ [0-9]+\b", torrent_name, re.IGNORECASE) or \
                re.search(r"\b(S|Seasons?) *[0-9]+ *(E|Ep|Episodes?|X) *[0-9]+ *(E|to)? *[0-9]+\b", torrent_name, re.IGNORECASE) or \
                re.search(r"\bS[0-9]+ [0-9]+\b", torrent_name, re.IGNORECASE) or \
                re.search(r"\bMissing episodes?\b", torrent_name, re.IGNORECASE):
            log.info('Result "%s" seem to not contain a full season', torrent_name)
            return True

        return False

    def is_single_episode_result(self, torrent_name):
        '''Check if the torrent only contains one episode'''

        if re.search(r"\b(S|Seasons?) *[0-9]+ *(E|Ep|Episodes?|X) *[0-9]+\b", torrent_name, re.IGNORECASE):
            log.info('Result "%s" seem to be a single episode', torrent_name)
            return True

        return False
    
    def get_season_number_list(self, torrent_name):
        '''Check if the torrent contains one or more seasons, and if so returns a list 
        of the season numbers it contains (empty list otherwise)'''

        season_number_list = list()

        m = re.search(r"\b(?:S|Seasons?|Complete) *([0-9]{1,2})"+ 30*r" *(?:S|through|to|and|&)? *([0-9]{1,2})?\b", torrent_name, re.IGNORECASE)
        if m:
            # Retreive extracted season numbers from regex
            for season_number in m.groups():
                if season_number is None:
                    # Reached last result
                    break
                season_number_list.append(int(season_number)) # regex extracts strings

            # Explicitly list all season numbers (for results like "season 1 5", add 2 3 4)
            season_number_list.sort()
            for i in xrange(len(season_number_list)-1):
                next_season_number = season_number_list[i]+1
                while next_season_number < season_number_list[i+1]:
                    season_number_list.append(next_season_number)
                    next_season_number += 1

        return season_number_list

    def is_all_seasons_result(self, torrent_name):
        '''Check if the torrent contains all seasons of a given series'''

        if re.search(r"\b(Complete series|All seasons|Complete boxset|Complete mini *series|Complete mini series|Complete edition|Full series)\b", \
                torrent_name, re.IGNORECASE):
            return True

        return False
    
    def search_episode_torrent(self, episode):
        '''Find a torrent for the provided episode, returns the Torrent object'''

        season = episode.season
        series = season.series

        # Run search engine query
        search_string = "s%02de%02d" % (season.number, episode.number)
        torrent_list = self.search_torrent_by_string(self.clean_name(series.name), search_string)
        
        # Isolate the right torrent
        torrent = None
        for torrent_result in torrent_list:
            if torrent_result.hash is None or torrent_result.seeds is None or torrent_result.seeds <= 0:
                log.info("Discarded result for lack of seeds or hash: %s", torrent_result)
            else:
                torrent = torrent_result

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


