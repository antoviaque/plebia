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

import libtorrent as lt
import time

from django.conf import settings

# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Classes ###########################################################

class Bittorrent:

    def __init__(self):
        '''Starts a bittorrent daemon'''

        log.info('Starting bittorrent client')

        self.cache_dir = settings.TORRENT_SEARCH_CACHE_DIR

        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.load_state()

        self.session.start_dht()

        self.params = {
            'save_path': settings.DOWNLOAD_DIR.encode('ascii'),
            'storage_mode': lt.storage_mode_t(2),
            'paused': False,
            'auto_managed': True,
            'duplicate_is_error': True}

        self.handle_dict = {}

    def load_state(self):
        '''Loads the session environment variables if available from cache'''

        session_data = self.get_cache('bt_session_data')
        if session_data is not None:
            log.info('Loading existing cached session')
            self.session.load_state(session_data)

    def save_state(self):
        '''Save a copy of the current sessions variables to the cache'''

        log.debug('Saving current session')
        self.set_cache('bt_session_data', self.session.save_state())

    def add_magnet(self, magnet_uri, cache=False):
        '''Schedule a magnet link for download. If cache=True, only add it if the metadata
        is not already in the cache'''

        # Convert to str which libtorrent expects
        magnet_uri = magnet_uri.encode('ascii')
        hash = magnet_uri[20:60]

        log.info('Adding to the download queue: %s', magnet_uri)

        # Prefer cached results if requested
        if cache and self.get_cache(hash):
            log.info('Torrent info found in cache for %s', magnet_uri)
            return False

        # Start polling metadata from network
        if hash not in self.handle_dict: # Check we aren't already processing this torrent
            handle = lt.add_magnet_uri(self.session, magnet_uri, self.params)
            self.handle_dict[hash] = handle
            self.save_state()

        return True

    def find_hash(self, hash):
        '''Return the handle for a given hash, if currently in the queue'''

        if hash in self.handle_dict:
            return self.handle_dict[hash]
        else:
            return None

    def remove_torrent(self, hash):
        '''Stop a torrent from downloading and remove it from the queue'''

        handle = self.find_hash(hash)
        if handle is None or not handle.is_valid():
            log.info('Could not find torrent handle for hash %s', hash)
            return False
        else:
            log.info('Removing torrent from queue for hash %s', hash)
            self.session.remove_torrent(handle)
            return True

    def get_status(self):
        '''Returns the current server status, including DHT'''

        return self.session.status()

    def get_torrent_info(self, hash, cache=False):
        '''Get current torrent status information for a given hash, if the metadata is 
        already available. See http://www.rasterbar.com/products/libtorrent/manual.html#torrent-info
        Returns None if hash isn't found, False if metadata isn't ready yet.'''

        # Return the cached version if asked to
        if cache:
            torrent_info = self.get_cache(hash)
            if torrent_info:
                log.info('Retreived torrent info *from cache* for hash %s: %s', hash, torrent_info)
                return torrent_info

        handle = self.find_hash(hash)
        if handle is None or not handle.is_valid():
            log.error('Error or invalid handle for hash %s', hash)
            torrent_info = None

        elif not handle.has_metadata():
            log.debug('Metadata not ready for hash %s', hash)
            torrent_info = False

        else:
            torrent_info = self.build_torrent_info(handle)
            log.info('Retreived torrent info for hash %s: %s', hash, torrent_info)
            self.set_cache(hash, torrent_info)

        self.save_state()
        return torrent_info

    def build_torrent_info(self, handle):
        '''Return corresponding native python objects for a torrent_info (for eg to allow caching)'''

        files = list()
        torrent_info = handle.get_torrent_info()
        for res_file in torrent_info.files():
            files.append({'path': unicode(res_file.path, 'utf-8'), 'size': res_file.size})

        status = {'list_seeds': handle.status().list_seeds}

        return {'files': files, 'status': status, 'name': torrent_info.name()}

    def get_cache(self, cache_id):
        '''Get a value from the cache'''

        import pickle, os

        cache_file = os.path.join(self.cache_dir, cache_id)
        if os.path.isfile(cache_file):
            with open(cache_file) as f:
                return pickle.load(f)

    def set_cache(self, cache_id, content):
        '''Set a value in the cache'''

        import pickle, os

        cache_file = os.path.join(self.cache_dir, cache_id)
        with open(cache_file, 'wb') as f:
            pickle.dump(content, f)

