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


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Functions #########################################################

def sane_text(text, length=0):
    '''Remove non-string characters from text, and optionally limit size to length characters (0 for no limit)'''

    if not isinstance(text, basestring):
        log.debug('Provided text is not a string "%s"', text)
        return ''

    # HTML NULL entity
    sane_text = text.replace(u'&#0', u'')

    # Nb of characters
    if length:
        sane_text = sane_text[:length]

    return sane_text


def get_url(url, sleep_time=2):
    '''Returns the content at the provided URL, None if error
    Pause for sleep_time seconds before making the request, to avoid spamming websites with requests'''

    import requests, time

    time.sleep(sleep_time)

    headers = {'User-Agent': 'Plebia/0.1'}
    r = requests.get(url, headers=headers)

    if r.status_code == requests.codes.ok:
        log.debug("Retreived URL %s => %s", url, r.content)
        return r.content
    else:
        log.debug("Could not retreive URL %s (error code=%d)", url, r.status_code)
        return None

def open_url(url):
    '''Returns a file handler to the provided URL'''

    import urllib

    return urllib.urlopen(url)

