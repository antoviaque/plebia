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
from plebia.wall.models import Video
from django.conf import settings

import re
import subprocess
import time
import os
import mimetypes


# Globals ###########################################################

DELAY = 5
FNULL = open(os.devnull, 'w')


# Main ##############################################################

class Command(BaseCommand):
    help = 'Runs the cron tasks, every second for 1 minute'

    def handle(self, *args, **options):
        start = time.time()
        next = start
        while next <= start+50-DELAY:
            video_update()

            next += DELAY
            time.sleep(next - time.time())


def video_update():
    # Get Video() objects which must be updated
    video_list = Video.objects.filter(\
            Q(status='New') | \
            Q(status='Transcoding'))\
            .order_by('-date_added')
    
    for video in video_list:
        if video.status == 'New':
            start_transcoding(video)

        elif video.status == 'Transcoding':
            update_transcoding_status(video)


# Transcoding #######################################################

def start_transcoding(video):
    prefix = video.original_path[:-4]
    video.webm_path = prefix + '.webm'
    video.mp4_path = prefix + '.mp4'
    video.ogv_path = prefix + '.ogv'
    video.image_path = prefix + '.jpg'

    # Generate thumbnail
    subprocess.Popen([settings.FFMPEG_PATH, '-i', os.path.join(settings.DOWNLOAD_DIR, video.original_path), '-ss', '120', '-vframes', '1', '-r', '1', '-s', '640x360', '-f', 'image2', settings.DOWNLOAD_DIR + video.image_path], stdout = FNULL, stderr = FNULL)
    # Convert to WebM
    subprocess.Popen([settings.FFMPEG_PATH, '-i', os.path.join(settings.DOWNLOAD_DIR, video.original_path), '-b', '1500k', '-acodec', 'libvorbis', '-ac', '2', '-ab', '96k', '-ar', '44100', '-s', '640x360', '-r', '18', settings.DOWNLOAD_DIR + video.webm_path], stdout = FNULL, stderr = FNULL)

    video.status = 'Transcoding'
    video.save()
    

def update_transcoding_status(video):
    '''Check if video transcoding is over'''

    retcode = subprocess.call([settings.BIN_DIR+"check_transcoding.sh", video.original_path])
    
    if retcode: # ffmpeg process not found, transcoding over
        video.status = 'Completed'
        video.save()


