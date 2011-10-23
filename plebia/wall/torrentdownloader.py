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
from django.db.models import Q
from django.conf import settings

import re
import subprocess


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
                Q(status='Downloading'))\
                .order_by('-date_added')

        # Refresh downloader status
        torrent_downloader = TorrentDownloader()
        torrent_downloader.update_torrent_list()

        for db_torrent in db_torrent_list:
            # Match the current torrent with information returned by deluge
            dl_torrent = torrent_downloader.get_torrent_by_hash(db_torrent.hash)

            # Update progress of downloading torrent
            if dl_torrent:
                db_torrent.update_from_torrent(dl_torrent)


class TorrentDownloader:

    def __init__(self):
        self.torrent_list = None

    def add_hash(self, hash):
        '''Start download of new torrents'''

        cmd = list(settings.DELUGE_COMMAND)
        cmd.append('add magnet:?xt=urn:btih:%s' % hash)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (result, errors) = p.communicate()

    def get_deluge_output(self):
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
                    torrent.download_speed = "0 KiB/s"

                # Upload speed
                m2 = re.search(r"Up Speed: (?P<upload_speed>\d+\.\d+ .iB.s)", m.group('state'))
                if m2:
                    torrent.upload_speed = m2.group('upload_speed')
                else:
                    torrent.upload_speed = "0 KiB/s"

                # ETA
                m2 = re.search(r"ETA: (?P<eta>.*)$", m.group('state'))
                if m2:
                    torrent.eta = m2.group('eta')
                else:
                    torrent.eta = ""

                # Progress isn't shown once completed
                m2 = re.match(r"Progress: (?P<torrent_progress>\d+\.\d+)", m.group('progress'))
                if m2:
                    torrent.progress = float(m2.group('torrent_progress'))
                else:
                    torrent.progress = 100.0

                # Status
                if torrent.progress == 100.0:
                    torrent.status = 'Completed'
                else:
                    torrent.status = 'Downloading'

                torrent_list.append(torrent)

        # Update
        self.torrent_list = torrent_list


    def get_torrent_by_hash(self, torrent_hash):
        for torrent in self.torrent_list:
            if torrent.hash == torrent_hash:
                return torrent
        return None




