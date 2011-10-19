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

from plebia.wall.torrentsearcher import TorrentSearchManager
from plebia.wall.torrentdownloader import TorrentDownloadManager
from plebia.wall.packagemanager import PackageManager
from plebia.wall.videotranscoder import VideoTranscodingManager
from plebia.wall.contentdbupdater import ContentDBUpdateManager

# Models ############################################################

class DownloadManager:
    '''Controls the different actions that can be performed on a content during its download/life'''

    def __init__(self):
        self.actions = {
                'torrent_search': TorrentSearchManager(),
                'torrent_download': TorrentDownloadManager(),
                'package_management': PackageManager(),
                'video_transcoding': VideoTranscodingManager(),
                'contentdb_update': ContentDBUpdateManager()
                }
    
    def get_actions_list(self):
        return self.actions.keys()

    def do(self, command):
        '''Execute a given action'''
        if command in self.actions:
            self.actions[command].do()

