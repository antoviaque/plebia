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

from django.db.models import Q
from plebia.wall.models import Video
from django.conf import settings

import subprocess
import os


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Globals ###########################################################

FNULL = open(os.devnull, 'w')


# Models ############################################################

class VideoTranscodingManager:
    '''Transcodes newly retreived videos'''

    def __init__(self):
        pass
    
    def do(self):
        '''Perform the maintenance'''

        # Get Video() objects which must be updated
        video_list = Video.objects.filter(\
                Q(status='New') | \
                Q(status='Queued') | \
                Q(status='Transcoding'))\
                .order_by('-date_added')
        
        for video in video_list:
            if video.status == 'New' or video.status == 'Queued':
                video.start_transcoding()

            elif video.status == 'Transcoding':
                video.update_transcoding_status()


class VideoTranscoder:

    def generate_thumbnail(self, video_path, image_path):
        '''Generate thumbnail'''

        log.info('Generating thumbnail for %s', video_path)

        p = subprocess.Popen([settings.FFMPEG_PATH, '-i', video_path, '-ss', '120', '-vframes', '1', '-r', '1', '-s', '640x360', '-f', 'image2', image_path], stdout = FNULL, stderr = FNULL)
        
        # Wait for thumb to be generated before continuing
        (result, errors) = p.communicate()
        
    def transcode_webm(self, video_src_path, video_dst_path):
        '''Convert to WebM'''

        log.info('Generating WebM video for %s', video_src_path)

        subprocess.Popen([settings.FFMPEG_PATH, '-i', video_src_path, '-b', '1500k', '-acodec', 'libvorbis', '-ac', '2', '-ab', '96k', '-ar', '44100', '-s', '640x360', '-r', '18', video_dst_path], stdout = FNULL, stderr = FNULL)

    def transcode_mp4(self, video_src_path, video_dst_path):
        pass

    def transcode_ogv(self, video_src_path, video_dst_path):
        pass

    def is_running(self, video_path):
        '''Check if video transcoding is over'''

        # If ffmpeg process is not found, transcoding over
        retcode = subprocess.call([settings.BIN_DIR+"check_transcoding.sh", video_path])

        return not retcode

    def has_free_slot(self):
        '''Can we start a new transcoding'''

        if self.nb_transcoding_processes() < settings.MAX_TRANSCODING_PROCESSES:
            return True
        else:
            return False

    def nb_transcoding_processes(self):
        '''How many transcoding processes are currently running'''

        cmd = [settings.BIN_DIR+"count_transcoding.sh"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (result, errors) = p.communicate()

        nb_transcoding_processes = int(result)
        return nb_transcoding_processes



