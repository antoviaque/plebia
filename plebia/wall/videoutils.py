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
from plebia.wall.models import Video, SeriesSeason

import re
import subprocess
import os
import mimetypes


# Finding Video objects in torrent packages #########################

def locate_video(episode):
    torrent = episode.torrent

    # The torrent base file path is determined by its name
    torrent_path = torrent.name

    # Check if the video has already been located for this torrent/episode
    if episode.video is not None:
        return episode.video

    video = Video()
    # If it's a season torrent, need to find the right episode file/directory first
    if torrent.type == 'season':
        season_path = locate_season_in_season_torrent(episode)
        torrent_path = locate_episode_in_season_torrent(episode, subpath=season_path)

        # If the episode path couldn't be found, we won't find the video for this torrent
        if torrent_path is None:
            video.status = 'Not found'
            video.save()
            return video

    # If the torrent is a single file, that's the one we want
    if os.path.isfile(os.path.join(settings.DOWNLOAD_DIR, torrent_path)):
        video.original_path = torrent_path
    # If the torrent is a directory, look inside
    elif os.path.isdir(os.path.join(settings.DOWNLOAD_DIR, torrent_path)):
        video_filename_list = get_videos_from_directory(torrent_path)
        if len(video_filename_list) == 0: 
            video.status = 'Not found'
            video.save()
            return video

        # Select the biggest video
        max_filename = None 
        max_size = 0
        for video_filename in video_filename_list:
            video_size = os.stat(os.path.join(settings.DOWNLOAD_DIR, video_filename))
            if video_size > max_size:
                max_filename = video_filename
                max_size = video_size

        video.original_path = max_filename

    # Save
    video.save()
    return video


def locate_season_in_season_torrent(episode, subpath=''):
    """A season torrent can contain several seasons - Register all seasons found and return path to the current episode's season"""

    torrent = episode.torrent
    torrent_path = os.path.join(torrent.name, subpath)
    torrent_dir = os.path.join(settings.DOWNLOAD_DIR, torrent_path)
    season = episode.season
    season_path = ''

    # Try to match the directories against a season name/number
    for filename in os.listdir(torrent_dir):
        if os.path.isdir(os.path.join(torrent_dir, filename)):
            # If the dir name matches a season name, get its number
            m1 = re.search(r"season[ -_\.]*([0-9])+", filename, re.IGNORECASE)
            m2 = re.search(r"s[ -_\.]*([0-9])+$", filename, re.IGNORECASE)
            if m1 is not None:
                number = int(m1.group(1))
            elif m2 is not None:
                number = int(m2.group(1))
            else:
                locate_season_in_season_torrent(episode, subpath=os.path.join(subpath, filename))
                continue

            # Register the torrent for this season if necessary
            cur_season = SeriesSeason.objects.get_or_create(number=number, series=season.series)[0]
            if cur_season.torrent is None:
                cur_season.torrent = torrent

            cur_season.save()

            # If it's the season we are looking for, return it
            if season.number == number:
                season_path = os.path.join(subpath, filename)

    return season_path


def locate_episode_in_season_torrent(episode, subpath=''):
    """A season contains several episodes - find the path to the one from the episode object (from within subpath)"""

    torrent = episode.torrent
    torrent_path = os.path.join(torrent.name, subpath)
    season = episode.season

    # Try to match the file/dirs against the episode number
    for filename in os.listdir(os.path.join(settings.DOWNLOAD_DIR, torrent_path)):
        if re.search(r"s%02de%02d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%de%02d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%de%d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%02de%d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%02d%02d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%d%02d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"s%d%d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"%d%02d" % (season.number, episode.number), filename, re.IGNORECASE) \
        or re.search(r"season[ -_\.0]*%d[ -_\.]*episode[ -_\.0]*%d" % (season.number, episode.number), filename, re.IGNORECASE):
            episode_path = os.path.join(torrent_path, filename)
            return episode_path

    return None
        

def get_videos_from_directory(dir_path):
    # First, extract files from archives in this directory to be able to find those files too
    extract_archives_in_directory(dir_path)

    video_filename_list = list()
    for filename_short in os.listdir(os.path.join(settings.DOWNLOAD_DIR, dir_path)):
        filename = os.path.join(dir_path, filename_short)

        # Go recursively into subdirectories
        if os.path.isdir(os.path.join(settings.DOWNLOAD_DIR, filename)):
            sub_list = get_videos_from_directory(filename)
            video_filename_list.extend(sub_list)

        # Keep a list of videos
        (file_type, file_encoding) = mimetypes.guess_type(os.path.join(settings.DOWNLOAD_DIR, filename))
        if file_type is not None and file_type.startswith('video'):
            video_filename_list.append(filename)

    return video_filename_list


def extract_archives_in_directory(dir_path):
    for filename_short in os.listdir(os.path.join(settings.DOWNLOAD_DIR, dir_path)):
        filename = os.path.join(settings.DOWNLOAD_DIR, dir_path, filename_short)

        # Change to the file directory (otherwise unrar extracts elsewhere)
        os.chdir(os.path.join(settings.DOWNLOAD_DIR, dir_path))

        # Uncompress any archives (rar)
        if filename.lower().endswith('.rar'):
            # Run unrar
            cmd = (settings.UNRAR_PATH, 'x', '-y', filename)
            (result, errors) = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()



