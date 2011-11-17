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
from django.db.models import Q
from django.conf import settings

import re
import subprocess


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Models ############################################################

class TorrentDownloadManager:
    '''Update statistics of downloads from deluge'''

    def __init__(self):
        pass


    def do(self):
        '''Perform the maintenance'''

        # Start downloading newly registered torrents
        self.start_torrents()

        # Update status of currently downloading torrents
        self.update_torrents()


    def start_torrents(self):
        '''Start downloading newly registered torrents'''
        
        # Get Torrent() objects which must be updated
        torrent_list = Torrent.objects.filter(\
                Q(status='New'))\
                .order_by('-date_added')

        for torrent in torrent_list:
            # Start the torrent download
            torrent.start_download()

    def update_torrents(self):
        '''Update status of currently downloading torrents'''

        # Get Torrent() objects which must be updated
        db_torrent_list = Torrent.objects.filter(\
                Q(status='Queued') | \
                Q(status='Downloading'))\
                .order_by('-date_added')

        # Refresh downloader status
        torrent_downloader = TorrentDownloader()
        torrent_downloader.update_torrent_list()

        # Cancel downloads which don't find seeds
        torrent_downloader.update_no_seed_timeout()

        for db_torrent in db_torrent_list:
            # Match the current torrent with information returned by deluge
            dl_torrent = torrent_downloader.get_torrent_by_hash(db_torrent.hash)

            # Update progress of downloading torrent
            if dl_torrent:
                db_torrent.update_from_torrent(dl_torrent)


class TorrentDownloader:

    def __init__(self):
        self.torrent_list = None

    def add_magnet(self, magnet):
        '''Start download of a new torrent using a magnet URI'''

        log.info("Asking torrent downloader to start downloading magnet %s", magnet)

        cmd = list(settings.DELUGE_COMMAND)
        cmd.append('add %s' % magnet)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (result, errors) = p.communicate()

    def cancel_hash(self, hash):
        '''Stop download of torrent'''

        log.info("Asking torrent downloader to STOP downloading hash %s", hash)

        cmd = list(settings.DELUGE_COMMAND)
        cmd.append('rm %s' % hash)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (result, errors) = p.communicate()

    def get_deluge_output(self):
        log.debug("Getting updated download status output from torrent downloader")

        cmd = list(settings.DELUGE_COMMAND)
        cmd.append('info')
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (output, errors) = p.communicate()
        return output

    def update_torrent_list(self):
        output = self.get_deluge_output()
        result_list = output.lstrip().split("\n \n")
        torrent_list = list()
        for result in result_list:
            torrent = Torrent()
            m = re.match(r"""Name: (?P<torrent_name>.+)
ID: (?P<torrent_hash>.+)
State: (?P<state>.+)
Seeds: (?P<seeds>.+)
Size: (?P<size>.+)
Seed time: (?P<seed_time>.+)
Tracker status:(?P<tracker_status>.+)\n?(?P<progress>.*)""", result, re.MULTILINE)

            if m:
                torrent.hash = m.group('torrent_hash')

                log.debug("Found status update for hash %s", torrent.hash)

                # Deluge shows hash as name until it can retreive it
                if m.group('torrent_name') != m.group('torrent_hash'):
                    torrent.name = m.group('torrent_name')
                else:
                    torrent.name = ''

                # Download speed
                m2 = re.search(r"Down Speed: (?P<download_speed>\d+\.\d+ .iB.s)", m.group('state'))
                if m2:
                    torrent.download_speed = m2.group('download_speed')
                else:
                    torrent.download_speed = "0.0 KiB/s"

                # Upload speed
                m2 = re.search(r"Up Speed: (?P<upload_speed>\d+\.\d+ .iB.s)", m.group('state'))
                if m2:
                    torrent.upload_speed = m2.group('upload_speed')
                else:
                    torrent.upload_speed = "0.0 KiB/s"

                # ETA
                m2 = re.search(r"ETA: (?P<eta>.*)$", m.group('state'))
                if m2:
                    torrent.eta = m2.group('eta')
                else:
                    torrent.eta = ""

                # Seeds & peers
                m2 = re.search(r"\d+ \((?P<seeds>\d+)\) Peers: \d+ \((?P<peers>\d+)\)", m.group('seeds'))
                if m2:
                    torrent.seeds = int(m2.group('seeds'))
                    torrent.peers = int(m2.group('peers'))
                else:
                    torrent.seeds = None
                    torrent.peers = None

                # Active time
                m2 = re.search(r"Active: (?P<active_time>.*)$", m.group('seed_time'))
                if m2:
                    torrent.active_time = m2.group('active_time')
                else:
                    torrent.active_time = ''

                # Progress isn't shown once completed
                m2 = re.match(r"Progress: (?P<torrent_progress>\d+\.\d+)", m.group('progress'))
                if m2:
                    torrent.progress = float(m2.group('torrent_progress'))
                else:
                    torrent.progress = 100.0

                # Status
                m2 = re.search(r"^(?P<state>[^ ]+).*$", m.group('state'))
                if m2:
                    # Do not care about queued seeding status, which for us is a completed status
                    if torrent.progress == 100.0:
                        if m2.group('state') == 'Downloading':
                            torrent.status = 'Downloading'
                        else:
                            torrent.status = 'Completed'
                    else:
                        if m2.group('state') == 'Queued':
                            torrent.status = 'Queued'
                        elif m2.group('state') == 'Downloading':
                            torrent.status = 'Downloading'
                        else:
                            torrent.status = 'Error'
                else:
                    torrent.status = 'Error'

                torrent_list.append(torrent)

        # Update
        self.torrent_list = torrent_list

    def update_no_seed_timeout(self):
        '''Cancel downloads which don't find seeds'''
        
        torrent_list = list()
        for torrent in self.torrent_list:
            if torrent.status == 'Downloading' and torrent.seeds == 0 and torrent.active_time[:9] != '0 days 00': # active download for more than 1h
                torrent.status = 'Error'
                self.cancel_hash(torrent.hash)
            
            torrent_list.append(torrent)

        self.torrent_list = torrent_list

    def get_torrent_by_hash(self, torrent_hash):
        for torrent in self.torrent_list:
            if torrent.hash == torrent_hash:
                return torrent
        return None




