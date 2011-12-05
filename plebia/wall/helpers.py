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

import time

# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Functions #########################################################

def sane_text(text, length=0):
    '''Remove non-string characters from text, and optionally limit size to length characters (0 for no limit)'''

    if not isinstance(text, basestring):
        log.debug('Provided text is not a string "%s"', text)
        return ''

    # Unicode conversion
    sane_text = text.decode('utf-8', 'replace')

    # HTML NULL entity
    sane_text = sane_text.replace(u'&#0', u'')

    # Nb of characters
    if length:
        sane_text = sane_text[:length]

    return sane_text

def get_url_json(url):
    '''Returns the python object corresponding to the JSON string
    retreived at the provided URL, None if error'''

    import json

    content = get_url(url)

    if content is None:
        return None
    
    try:
        answer = json.loads(content)
        log.debug("Loaded JSON '%s'", answer)
    except ValueError:
        log.warn("Could not load JSON from '%s'", content)
        return None

    return answer

def get_url_rss(url):
    '''Returns the list of entries from the RSS feed retreived
    at the provided URL, None if error'''

    import feedparser

    content = get_url(url)

    if content is None:
        return None
    
    # Get the list of torrents results
    res = feedparser.parse(content)
    if not res.entries:
        log.info("No results found for URL %s", url)
        return list()

    return res.entries

def get_url(url):
    '''Returns the content at the provided URL, None if error'''

    import requests

    # Pause before making the request, to avoid spamming websites
    time.sleep(settings.HTTP_REQUESTS_DELAY)

    headers = {'User-Agent': settings.SOFTWARE_USER_AGENT}
    r = requests.get(url, headers=headers, proxies=settings.PROXIES)

    if r.status_code == requests.codes.ok:
        log.debug("Retreived URL %s => %s", url, r.content)
        return r.content
    else:
        log.debug("Could not retreive URL %s (error code=%d)", url, r.status_code)
        return None

def open_url(url):
    '''Returns a file handler to the provided URL
    Warning: no pause between requests (FIXME)'''

    import urllib

    # Set user agent
    class AppURLopener(urllib.FancyURLopener):
        version = settings.SOFTWARE_USER_AGENT
    urllib._urlopener = AppURLopener()

    return urllib.urlopen(url, proxies=settings.PROXIES)

def mkdir_p(path):
    '''Recursive mkdir that doesn't fail when the directory already exists'''

    import os, errno

    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise


