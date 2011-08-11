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

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from plebia.wall.models import Torrent
from django.conf import settings

import re
import subprocess
import time


# Globals ###########################################################

DELAY = 5


# Main ##############################################################

class Command(BaseCommand):
    help = 'Runs the cron tasks, every second for 1 minute'

    def handle(self, *args, **options):
        start = time.time()
        next = start
        while next <= start+50-DELAY:
            torrent_update()

            next += DELAY
            time.sleep(next - time.time())


def torrent_update():
    # Get current torrents status from deluge
    deluge_output = get_deluge_output()
    deluge_torrent_list = parse_deluge_output(deluge_output)

    # Get Torrent() objects which must be updated
    torrent_list = Torrent.objects.filter(\
            Q(status='New') | \
            Q(status='Downloading'))\
            .order_by('-date_added')

    for torrent in torrent_list:
        # Match the current torrent with information returned by deluge
        deluge_torrent_info = get_deluge_torrent_by_hash(deluge_torrent_list, torrent.hash)

        # Start new torrent
        if torrent.status == 'New':
            start_download(torrent)
            torrent.status = 'Downloading'

        # Update progress of downloading torrent
        elif torrent.status == 'Downloading' and deluge_torrent_info:
            update_download_progress(torrent, deluge_torrent_info)

            # Start video processing of completed torrent
            if torrent.progress == 100.0:
                torrent.status = 'Completed'

        # Save
        torrent.save()


# Deluge & Torrent download progress ################################

def start_download(torrent):
    '''Start download of new torrents'''

    cmd = list(settings.DELUGE_COMMAND)
    cmd.append('add magnet:?xt=urn:btih:%s' % torrent.hash)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (result, errors) = p.communicate()

def get_deluge_output():
    cmd = list(settings.DELUGE_COMMAND)
    cmd.append('info')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (output, errors) = p.communicate()
    return output

def parse_deluge_output(output):
    result_list = output.lstrip().split("\n \n")
    torrent_list = list()
    for result in result_list:
        torrent = dict()
        m = re.match(r"""Name: (?P<torrent_name>.+)
ID: (?P<torrent_hash>.+)
State: (?P<state>.+)
Seeds: (?P<seeds>.+)
Size: (?P<size>.+)
Seed time: (?P<seed_time>.+)
Tracker status:(?P<tracker_status>.+)\n?(?P<progress>.*)""", result, re.MULTILINE)

        if m:
            torrent['torrent_hash'] = m.group('torrent_hash')

            # Deluge shows hash as name until it can retreive it
            if m.group('torrent_name') != m.group('torrent_hash'):
                torrent['torrent_name'] = m.group('torrent_name')
            else:
                torrent['torrent_name'] = None

            # Progress isn't shown once completed
            m2 = re.match(r"Progress: (?P<torrent_progress>\d+\.\d+)", m.group('progress'))
            if m2:
                torrent['torrent_progress'] = float(m2.group('torrent_progress'))
            else:
                torrent['torrent_progress'] = 100.0

            torrent_list.append(torrent)

    return torrent_list


def get_deluge_torrent_by_hash(torrent_list, torrent_hash):
    for torrent in torrent_list:
        if torrent['torrent_hash'] == torrent_hash:
            return torrent
    return None


def update_download_progress(torrent, deluge_torrent_info):
    '''Update status of downloading torrents'''

    # FIXME Check for torrent errors
    torrent.progress = deluge_torrent_info['torrent_progress']
   
    # As soon as we get the torrent name, update it
    if deluge_torrent_info['torrent_name'] and torrent.name == "":
        torrent.name = deluge_torrent_info['torrent_name']
    
    torrent.save()



