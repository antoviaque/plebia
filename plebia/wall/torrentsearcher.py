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
from plebia.wall.models import Episode, Torrent

from lxml.html import soupparser
from lxml.cssselect import CSSSelector

import re
import mechanize
import time
import datetime


# mechanize #########################################################

cookies = mechanize.CookieJar()
opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cookies))
opener.addheaders = [("User-agent", "Mozilla/5.0 (compatible; Plebia/0.1)")]
mechanize.install_opener(opener)


# Models ############################################################

class TorrentSearchManager:
    '''Search torrent of new episodes & start download'''

    def __init__(self):
        pass
    
    def do(self):
        '''Perform the maintenance'''
        
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        
        # Get new episodes for which we must find a torrent file
        new_episode_list = Episode.objects.filter(\
                Q(torrent=None))\
                .filter(first_aired__lte=yesterday)\
                .order_by('date_added')

        for new_episode in new_episode_list:
            # Get the episode to create its torrent 
            # (eventually searching for it through methods from here)
            new_episode.get_or_create_torrent()



