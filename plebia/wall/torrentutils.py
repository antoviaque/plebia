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

from plebia.wall.models import Torrent

from lxml.html import soupparser
from lxml.cssselect import CSSSelector

import re
import mechanize


# Helpers - Finding torrents ########################################

def get_torrent_by_episode(episode):
    season = episode.season
    series = season.series

    # Check if the full season is not already there
    if season.torrent is not None:
        torrent = season.torrent
    else:
        # Try to get the single epside first
        search_string = "(tv|television) %s s%02de%02d" % (series.name, season.number, episode.number)
        torrent = get_torrent_by_search(search_string)

        # Otherwise try to get the full season
        if torrent is None or torrent.seeds < 10:
            search_string = "(tv|television) %s season %d" % (series.name, season.number)
            torrent = get_torrent_by_search(search_string)
            torrent.type = 'season'
            torrent.save()

            season.torrent = torrent
            season.save()
        else:
            torrent.type = 'episode'
            torrent.save()

    return torrent


def get_torrent_by_search(search_string):
    torrent = Torrent()
    html_result = submit_form("http://torrentz.eu/", search_string)

    # First check if any torrent was found at all
    if(re.search("Could not match your exact query", html_result)):
        return None
    
    # Get the list of torrents results
    root = soupparser.fromstring(html_result)
    sel = CSSSelector(".results dl")
    element = sel(root)
    if element is None:
        return None
    else:
        # Build the torrent object
        torrent.hash = element[0].cssselect("dt a")[0].get("href")[1:]
        torrent.seeds = element[0].cssselect("dd .u")[0].text_content().translate(None, ',')
        torrent.peers = element[0].cssselect("dd .d")[0].text_content().translate(None, ',')
        if torrent.hash is None or torrent.seeds is None or torrent.seeds <= 0:
            return None
        else:
            torrent.save()
            return torrent


def submit_form(url, text):
    br = mechanize.Browser()
    br.open(url)

    br.select_form(nr=0)
    br["f"] = text
    response = br.submit()
    html_result = response.get_data()

    return html_result



