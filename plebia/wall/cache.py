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

from wall.helpers import mkdir_p

import pickle, os

# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Functions #########################################################

def get_cache(cache_id):
    '''Get a value from the cache'''

    cache_file = os.path.join(settings.CACHE_DIR, cache_id)
    if os.path.isfile(cache_file):
        log.debug('Cache for %s FOUND', cache_file)
        with open(cache_file) as f:
            return pickle.load(f)
    else:
        log.debug('Cache for %s NOT found', cache_file)

    return None

def set_cache(cache_id, content):
    '''Set a value in the cache'''

    mkdir_p(settings.CACHE_DIR)

    cache_file = os.path.join(settings.CACHE_DIR, cache_id)
    with open(cache_file, 'wb') as f:
        pickle.dump(content, f)


