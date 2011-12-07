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

from django.conf import settings

from wall.helpers import normalize_text
from wall.models import Series

import re

# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Functions #########################################################

class TorrentMagic:
    '''Attempts to guess the contents of a torrent which hasn't been
    retreived yet'''

    def __init__(self, torrent, series_name=None):
        '''Builds the object based on a Torrent object, to be analyzed
        Optionally takes a series_name argument, to also perform sanity 
        checks about the series name'''

        # Attributes
        self.torrent = torrent
        self.torrent_name = normalize_text(self.torrent.name) # Remove non-letter characters like '.,-' etc
        self.series_name = series_name

        self.similar_series = None
        self.iso = None
        self.other_language = None
        self.partial_season = None
        self.complete_series = None
        self.season_number_list = None

        # Perform all checks
        self.analyze()

    def analyze(self):
        self.check_similar_series()
        self.check_unrelated_series()
        self.check_iso()
        self.check_language()
        self.check_partial_season()

        # Don't try to look for seasons on units smaller than a season
        if self.partial_season:
            self.complete_series = False
            self.season_number_list = list()
        else:
            # First, try to see if it contains all seasons, otherwise identify individual seasons
            # (can't get the list of individual seasons if it contains them all, since we don't know
            # how many seasons this series has)
            if not self.check_complete_series():
                self.check_season_number_list()
            else:
                self.season_number_list = list()

    def check_similar_series(self):
        '''Check if the torrent seem to be about a series with a similar series name'''

        # Only if we have the series name
        if self.series_name is None:
            return None

        # Series whose name contains the name of the series we are looking for
        similar_series_list = Series.objects.filter(name__icontains=self.series_name).exclude(name__iexact=self.series_name)

        self.similar_series = False
        for similar_series in similar_series_list:
            similar_match = re.search(similar_series.name, self.torrent_name, re.IGNORECASE)
            if similar_match:
                log.info('Torrent "%s" seem to be about series "%s"', self.torrent, similar_series.name)
                self.similar_series = True

        return self.similar_series

    def check_unrelated_series(self):
        '''Check if the torrent name contains the name of the series - otherwise it means this is about an unrelated series'''

        # Only if we have the series name
        if self.series_name is None:
            return None

        if not re.search(self.series_name, self.torrent_name, re.IGNORECASE):
            log.info('Torrent "%s" seem to be about an unrelated series (could not find the series name in torrent title)', self.torrent)
            self.unrelated_series = True
        else:
            self.unrelated_series = False

        return self.unrelated_series

    def check_iso(self):
        '''Check is the torrent seem to contain an ISO file'''

        if re.search(r"\b(disk|disc|iso)\b", self.torrent_name, re.IGNORECASE):
            log.info('Torrent "%s" seem to be an ISO', self.torrent)
            self.iso = True
        else:
            self.iso = False

        return self.iso

    def check_language(self):
        # Discard results in other languages
        if re.search(r"\b(ITA|NL|FR|FRENCH|DUTCH)\b", self.torrent_name, re.IGNORECASE):
            log.info('Torrent "%s" seem to be in another language', self.torrent)
            self.other_language = True
        else:
            self.other_language = False

        return self.other_language

    def check_partial_season(self):
        '''Check if the torrent does not seem to contain a whole season'''

        if re.search(r"\b(Ep|Episodes?) *[0-9]+ [0-9]+\b", self.torrent_name, re.IGNORECASE) or \
                re.search(r"\b(S|Seasons?) *[0-9]+ *(E|Ep|Episodes?|X) *[0-9]+ *(E|to)? *[0-9]+\b", self.torrent_name, re.IGNORECASE) or \
                re.search(r"\b(S|Seasons?) *[0-9]+ *(E|Ep|Episodes?|X) *[0-9]+\b", self.torrent_name, re.IGNORECASE) or \
                re.search(r"\bS[0-9]+ [0-9]+\b", self.torrent_name, re.IGNORECASE) or \
                re.search(r"\b(S|)[0-9]+(X|E)[0-9]+\b", self.torrent_name, re.IGNORECASE) or \
                re.search(r"\bMissing episodes?\b", self.torrent_name, re.IGNORECASE):
            log.info('Torrent "%s" seem to not contain a full season', self.torrent)
            self.partial_season = True
        else:
            self.partial_season = False

        return self.partial_season

    def check_complete_series(self):
        '''Check if the torrent seem to contain all seasons of a given series'''

        if re.search(r"\b(Complete series|All series|All seasons|Complete boxset|Complete mini *series|Complete mini series|Complete edition|Full series)\b", \
                self.torrent_name, re.IGNORECASE):
            self.complete_series = True
        else:
            self.complete_series = False

        return self.complete_series
    
    def check_season_number_list(self):
        '''Check if the torrent contains one or more seasons, and if so build a list 
        of the season numbers it contains (empty list otherwise)'''

        self.season_number_list = list()

        m = re.search(r"\b(?:S|Seasons?|Complete) *([0-9]{1,2})"+ 30*r" *(?:S|through|to|and|&)? *([0-9]{1,2})?\b", self.torrent_name, re.IGNORECASE)
        if m:
            # Retreive extracted season numbers from regex
            for season_number in m.groups():
                if season_number is None:
                    # Reached last result
                    break
                self.season_number_list.append(int(season_number)) # regex extracts strings

            # Explicitly list all season numbers (for results like "season 1 5", add 2 3 4)
            self.season_number_list.sort()
            for i in xrange(len(self.season_number_list)-1):
                next_season_number = self.season_number_list[i]+1
                while next_season_number < self.season_number_list[i+1]:
                    self.season_number_list.append(next_season_number)
                    next_season_number += 1
            self.season_number_list.sort()

        return self.season_number_list


