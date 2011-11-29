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

from wall.models import Torrent
from wall.cache import get_cache, set_cache
from django.db.models import Q
from django.conf import settings

import libtorrent as lt
import time
import re
import subprocess


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Models ############################################################

class TorrentDownloadManager:
    '''Bittorrent client'''

    def __init__(self):
        self.bt = None

    def check_started(self):
        '''Check if the bittorrent client is already started, and start it if not'''

        if self.bt is None:
            self.bt = Bittorrent()
            self.resume_downloads()

    def resume_downloads(self):
        '''Use model states to know which torrents were running the last time
        the download manager was running'''

        torrent_list = Torrent.objects.filter(\
                Q(status='Downloading metadata') | \
                Q(status='Downloading'))\
                .order_by('-date_added')

        for torrent in torrent_list:
            # Reset downloads (libtorrent will find the files and resume on his own)
            torrent.set_status('New')

    def do(self):
        '''Do the periodic update'''

        # Make sure the BT client is started
        # Doing it now allows to make sure a BT client is only started for torrent_download
        # and not for the other maintenance routines (each of them is started in his own process)
        self.check_started()

        # Save current DHT state to allow to retreive it later if restarted
        self.bt.save_dht_state()

        # Log
        log.info("Remaining torrents: %d, DHT: %d, DL: %d, DHT: %s, queue: %s", \
                    Torrent.processing_objects.count(), \
                    Torrent.objects.filter(Q(status='New')|Q(status='Downloading metadata')).count(), \
                    Torrent.objects.filter(Q(status='Queued')|Q(status='Downloading')).count(), \
                    self.bt.dht_stats(), \
                    self.bt.queue_stats())

        # Update currently downloading torrents (& mark ones completed)
        self.update_downloading_torrents()

        # Start queued downloads when there's room
        self.update_queued_torrents()

        # Queue torrents for which metadata has been received,
        # Cancel torrents for which metadata retrieval takes too long
        self.update_downloading_metadata_torrents()

        # Start downloading metadata for new torrents when there is room
        self.start_metadata_downloads()

    def start_metadata_downloads(self):
        '''Start downloading metadata for new torrents when there is room'''
        
        torrent_list = Torrent.objects.filter(\
                Q(status='New'))\
                .order_by('last_status_change')

        for torrent in torrent_list:
            if self.has_free_metadata_slot():
                log.info("Starting to retrieve metadata for torrent %s", torrent)
                self.bt.add_magnet(torrent.get_magnet())
                torrent.set_status('Downloading metadata')

    def has_free_metadata_slot(self):
        '''Check if there is room for adding a new metadata download'''
        
        return Torrent.objects.filter(status='Downloading metadata').count() < settings.BITTORRENT_MAX_METADATA_DOWNLOADS

    def update_downloading_metadata_torrents(self):
        '''See if torrents currently downloading metadata need update'''

        torrent_list = Torrent.objects.filter(\
                Q(status='Downloading metadata'))\
                .order_by('last_status_change')

        for torrent in torrent_list:
            # Update misc info of torrent
            torrent_bt = self.bt.get_torrent_info(torrent)
            torrent.update_from_torrent(torrent_bt)

            # Cancel torrents for which metadata retrieval takes too long 
            if torrent.is_timeout(settings.BITTORRENT_METADATA_TIMEOUT):
                log.warn("Did not retreive metadata in time for torrent %s, cancelling.", torrent)
                self.bt.remove_hash(torrent.hash)

                torrent.set_status('Error')
                torrent.seeds = -1 # Differentiate from those with metadata but without seeds
                torrent.save()

            # Queue torrents for which metadata has been received
            if torrent_bt.has_metadata:
                log.info("Retrieved metadata for torrent %s", torrent)
                self.bt.remove_hash(torrent.hash)
                torrent.set_status('Queued')

    def update_queued_torrents(self):
        '''Start queued downloads when there's room'''

        torrent_list = Torrent.objects.filter(\
                Q(status='Queued')) \
                .order_by('last_status_change')

        for torrent in torrent_list:
            if self.has_free_download_slot():
                log.info("Starting to download torrent %s", torrent)
                self.bt.add_magnet(torrent.get_magnet())
                torrent.set_status('Downloading')

    def has_free_download_slot(self):
        '''Check if there is room for adding a new download (does not include metadata downloads)'''
        
        return Torrent.objects.filter(status='Downloading').count() < settings.BITTORRENT_MAX_DOWNLOADS

    def update_downloading_torrents(self):
        '''Update currently downloading torrents'''

        torrent_list = Torrent.objects.filter(\
                Q(status='Downloading'))\
                .order_by('last_status_change')
        
        for torrent_db in torrent_list:
            torrent_bt = self.bt.get_torrent_info(torrent_db)

            # Mark torrents which are completed
            if torrent_bt.status == 'Completed':
                log.info("Completed downloading torrent %s", torrent_db)
                torrent_db.set_status('Completed')

            # Cancel downloads which don't find seeds/error, etc.
            elif torrent_bt.status == 'Error':
                log.warn("Error downloading torrent %s", torrent_db)
                self.bt.remove_hash(torrent_db.hash)
                torrent_db.set_status('Error')

            # Cancel downloads still without seeds after some time
            elif torrent_db.is_timeout(settings.BITTORRENT_DOWNLOAD_NOSEED_TIMEOUT) and torrent_bt.seeds == 0:
                log.warn("No seeds found for torrent %s", torrent_db)
                self.bt.remove_hash(torrent_db.hash)
                torrent_db.set_status('Error')

            # Update misc info of torrent
            torrent_db.update_from_torrent(torrent_bt)


class Bittorrent:

    def __init__(self):
        '''Starts a bittorrent client'''

        log.info('Starting bittorrent client')

        # Settings
        self.session = lt.session()
        session_settings = lt.session_settings()
        session_settings.user_agent = '%s libtorrent/%d.%d' % (settings.SOFTWARE_USER_AGENT, lt.version_major, lt.version_minor)
        session_settings.active_downloads = settings.BITTORRENT_MAX_DOWNLOADS + settings.BITTORRENT_MAX_METADATA_DOWNLOADS
        session_settings.active_seeds = settings.BITTORRENT_MAX_SEEDS
        session_settings.active_limit = settings.BITTORRENT_MAX_DOWNLOADS + settings.BITTORRENT_MAX_SEEDS + settings.BITTORRENT_MAX_METADATA_DOWNLOADS
        self.session.set_settings(session_settings)

        # Start BT server
        ports = settings.BITTORRENT_PORTS
        self.session.listen_on(ports[0], ports[1])

        # Start DHT server
        dht_data = get_cache('bt_dht_data')
        self.session.start_dht(dht_data)

        self.params = {
            'save_path': settings.DOWNLOAD_DIR.encode('ascii'), # FIXME: support non-ascii characters
            'storage_mode': lt.storage_mode_t(2),
            'paused': False,
            'auto_managed': True,
            'duplicate_is_error': True}

        self.handle_dict = {}

    def save_dht_state(self):
        '''Save a copy of the current DHT state to the cache'''

        log.debug('Saving current DHT session')
        set_cache('bt_dht_data', self.session.dht_state())

    def add_magnet(self, magnet_uri):
        '''Schedule a magnet link for download'''

        # Convert to str which libtorrent expects
        magnet_uri = magnet_uri.encode('ascii')
        hash = magnet_uri[20:60]

        if hash not in self.handle_dict: # Check we aren't already processing this torrent
            log.info('Adding to the download queue: %s', magnet_uri)
            handle = lt.add_magnet_uri(self.session, magnet_uri, self.params)
            self.handle_dict[hash] = handle
        else:
            log.error('Already in the download queue: %s', magnet_uri)

        return True

    def get_handle_for_hash(self, hash):
        '''Return the handle for a given hash, if currently in the queue'''

        if hash in self.handle_dict:
            return self.handle_dict[hash]
        else:
            return None

    def remove_hash(self, hash):
        '''Stop a torrent from downloading and remove it from the queue'''

        handle = self.get_handle_for_hash(hash)
        if handle is None or not handle.is_valid():
            log.info('Could not find torrent handle for hash %s', hash)
            return False
        else:
            log.info('Removing torrent from queue for hash %s', hash)
            self.session.remove_torrent(handle)
            del(self.handle_dict[hash])
            return True

    def get_torrent_info(self, torrent_db):
        '''Returns a Torrent() object containing miscanealous info about the torrent
        State is either: 'Downloading', 'Completed' or 'Error'.'''

        import json
        from datetime import timedelta

        torrent_bt = Torrent()
        handle = self.get_handle_for_hash(torrent_db.hash)
        status = handle.status()

        # Status
        log.debug('Built torrent info for BT hash %s (status = %s, error = %s)', torrent_db.hash, status.state, status.error)
        if 'seeding' in str(status.state):
            torrent_bt.status = 'Completed'
        elif status.error:
            torrent_bt.status = 'Error'
        else:
            torrent_bt.status = 'Downloading'

        # Metadata
        torrent_bt.has_metadata = handle.has_metadata()
        if not torrent_bt.has_metadata:
            return torrent_bt

        info = handle.get_torrent_info()
        torrent_bt.name = info.name()
        torrent_bt.progress = status.progress
        torrent_bt.download_speed = "%.3f MB/s" % (status.download_rate/(1024*1024))
        torrent_bt.upload_speed = "%.3f MB/s" % (status.upload_rate/(1024*1024))
        torrent_bt.active_time = status.active_time
        torrent_bt.seeds = status.list_seeds
        torrent_bt.peers = status.list_peers

        # ETA
        size_left = info.total_size() - status.total_done
        if status.download_rate > 0:
            torrent_bt.eta = size_left / status.download_rate
        else:
            torrent_bt.eta = None

        # Files
        file_list = list()
        for res_file in info.files():
            file_list.append({'path': unicode(res_file.path, 'utf-8'), 'size': res_file.size})
        torrent_bt.file_list = json.dumps(file_list)

        return torrent_bt

    def get_status(self):
        '''Returns the current server status, including DHT'''

        return self.session.status()

    def dht_stats(self):
        '''Returns statistics about the current state of the DHT communications'''
        
        status = self.session.status()
        return { 
                'dht_nodes': status.dht_nodes, 
                'dht_node_cache': status.dht_node_cache,
                'dht_torrents': status.dht_torrents,
                'dht_global_nodes': status.dht_global_nodes
               }

    def queue_stats(self):
        '''Returns statistics about the torrents currently in the queue'''

        status = {}
        paused = 0
        for torrent_handle in self.session.get_torrents():
            # Number of paused torrents
            if torrent_handle.is_paused():
                paused +=1

            # Number of torrents in each state
            state = torrent_handle.status().state
            if state in status:
                status[state] += 1
            else:
                status[state] = 1

        return {
                'status': status,
                'paused': paused
                }


