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

from django.db.models import Q
from django.conf import settings
from wall.models import Series, Episode, Torrent

from lxml.html import soupparser
from lxml.cssselect import CSSSelector

import re
import mechanize
import time
import datetime


# mechanize #########################################################

cookies = mechanize.CookieJar()
opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cookies))
opener.addheaders = [("User-agent", "Mozilla/5.0 (compatible; %s)" % settings.SOFTWARE_USER_AGENT)]
mechanize.install_opener(opener)


# Models ############################################################

class TorrentSearchManager:
    '''Search torrent of new episodes & start download'''

    def __init__(self):
        pass
    
    def do(self):
        '''Perform the maintenance'''

        # Retreive new series (newly added, no episode retreived yet)
        self.search_new_series()

        # Retreive new episodes (previously added series)
        self.search_new_episodes()

    def search_new_series(self):
        '''Get new series, for which to search bulk season(s) packages'''

        # Series for which none of the episodes have an attached torrent yet
        new_series_list = Series.objects.exclude(season__episode__torrent__isnull=False)\
                .order_by('date_added')

        for new_series in new_series_list:
            new_series.find_torrent()

    def search_new_episodes(self):
        '''Get new episodes for which we must find a torrent file'''

        yesterday = datetime.date.today() - datetime.timedelta(days=1, hours=10)
        new_episode_list = Episode.objects.filter(\
                Q(torrent=None))\
                .filter(first_aired__lte=yesterday)\
                .order_by('date_added')

        for new_episode in new_episode_list:
            new_episode.find_torrent()



