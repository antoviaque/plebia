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
from plebia.wall.models import Torrent, Episode, Video
from django.conf import settings

import re
import subprocess
import os
import mimetypes


# Models ############################################################

class PackageManager:
    '''Find episodes videos in completed torrents'''

    def __init__(self):
        pass
    
    def do(self):
        '''Perform the maintenance'''

        # Get episodes for which we have a completed torrent but no video
        episode_list = Episode.objects.filter(\
                Q(video=None))\
                .filter(torrent__status__exact='Completed')\
                .order_by('date_added')

        for episode in episode_list:
            episode.get_or_create_video()


class Package:

    def __init__(self, torrent, path=''):
        '''Init a package from subfolder/file (sub_path) from the root of a torrent'''

        self.torrent = torrent
        
        # The torrent base file path is determined by its name
        if path:
            self.full_path = os.path.join(self.get_torrent_path(), path)
        else:
            self.full_path = self.get_torrent_path()

        self.path = path

    def get_torrent_path(self):
        '''Full system path of the torrent files root'''

        return os.path.join(settings.DOWNLOAD_DIR, self.torrent.name)


class MultiSeasonPackage(Package):

    def find_video(self, episode):
        '''Locates the video file of an episode within the package'''

        # Package potentially contains multiple seasons
        season_package = self.find_season_package(episode.season)

        if season_package == None:
            # Could also actually be a single season package
            season_package = SeasonPackage(self.torrent, self.path)
        
        video = season_package.find_video(episode)

        return video

    def find_season_package(self, season, sub_path=''):
        '''Locates the package of a specific season within the current package'''

        # Try to match the directories against a season name/number
        for filename in os.listdir(os.path.join(self.full_path, sub_path)):
            if os.path.isdir(os.path.join(self.full_path, sub_path, filename)):
                # If the dir name matches a season name, get its number
                m1 = re.search(r"season[ -_\.]*([0-9])+", filename, re.IGNORECASE)
                m2 = re.search(r"s[ -_\.]*([0-9])+$", filename, re.IGNORECASE)
                if m1 is not None:
                    number = int(m1.group(1))
                elif m2 is not None:
                    number = int(m2.group(1))
                else:
                    season_package = self.find_season_package(season, sub_path=os.path.join(sub_path, filename))
                    if season_package is not None:
                        return season_package
                    else:
                        continue

                # If it's the season we are looking for, build the season package to return
                if season.number == number:
                    season_package = SeasonPackage(self.torrent, os.path.join(self.path, sub_path, filename))
                    return season_package

        return None


class SeasonPackage(Package):

    def find_video(self, episode):
        '''Locates the video file of an episode within the package'''

        # Package contains multiple episodes
        episode_package = self.find_episode_package(episode)

        if episode_package == None:
            video = Video.objects.get_not_found_video()
        else:
            video = episode_package.find_video(episode)

        return video

    def clean_name(self, name):
        '''Replace separators by a single space'''

        return re.sub(r'[_\W]+', ' ', name).strip()

    def find_episode_package(self, episode, sub_path=''):
        '''Locates the package of a specific episode within the current package'''

        season = episode.season

        # Some extensions are missing from mime.types files
        mimetypes.add_type('video/mp4', '.m4v')
        mimetypes.add_type('video/rmvb', '.rmvb')

        for filename in os.listdir(os.path.join(self.full_path, sub_path)):
            # Build a filename where separators are spaces
            clean_filename = self.clean_name(filename)
            clean_episode_name = self.clean_name(episode.name)

            # Try to match the file/dirs against the episode number
            if re.search(clean_episode_name, clean_filename, re.IGNORECASE) \
                or re.search(r"\bs* *0*%d *[xe]* *0*%d\b" % (season.number, episode.number), clean_filename, re.IGNORECASE) \
                or re.search(r"\bseason *0*%d *episode *0*%d\b" % (season.number, episode.number), clean_filename, re.IGNORECASE) \
                or re.search(r"(^|[^0-9 ] +)0*%d +[^0-9 ]" % episode.number, clean_filename, re.IGNORECASE):
                # Check that this is a video or a folder
                (file_type, file_encoding) = mimetypes.guess_type(os.path.join(self.full_path, sub_path, filename))
                if (file_type is not None and file_type.startswith('video')) \
                        or os.path.isdir(os.path.join(self.full_path, sub_path, filename)):
                    episode_package = EpisodePackage(self.torrent, os.path.join(self.path, sub_path, filename))
                    return episode_package

            # Look for episodes recursively in folders
            if os.path.isdir(os.path.join(self.full_path, sub_path, filename)):
                episode_package = self.find_episode_package(episode, os.path.join(sub_path, filename))
                if episode_package is not None:
                    return episode_package

        return None


class EpisodePackage(Package):

    def find_video(self, episode):
        '''Locates the video object of an episode within the package'''

        video = Video()

        # If the torrent is a single file, that's the one we want
        if os.path.isfile(self.full_path):
            if self.path:
                video.original_path = os.path.join(self.torrent.name, self.path)
            else:
                video.original_path = self.torrent.name
        # If the torrent is a directory, look inside
        elif os.path.isdir(self.full_path):
            # First, extract files from archives in this directory to be able to find those files too
            self.extract_archives()

            # Get all video files
            video_filename_list = self.get_video_list()
            if len(video_filename_list) == 0: 
                return Video.objects.get_not_found_video()

            # Select the biggest video
            max_filename = None 
            max_size = 0
            for video_filename in video_filename_list:
                video_size = os.stat(os.path.join(self.full_path, video_filename)).st_size
                if video_size > max_size:
                    max_filename = video_filename
                    max_size = video_size

            # Check if there was any video at all
            if max_filename is not None:
                video.original_path = os.path.join(self.torrent.name, self.path, max_filename)
            else:
                video = Video.objects.get_not_found_video()
        else:
            video = Video.objects.get_not_found_video()

        # Save
        video.save()
        return video

    def extract_archives(self, sub_path=''):
        '''Extract all archives in current package, including subdirectories'''

        for filename in os.listdir(os.path.join(self.full_path, sub_path)):
            # Look recursively
            if os.path.isdir(os.path.join(self.full_path, sub_path, filename)):
                self.extract_archives(os.path.join(sub_path, filename))

            # Change to the file directory (otherwise unrar extracts elsewhere)
            os.chdir(os.path.join(self.full_path, sub_path))

            # Uncompress any archives (rar)
            if filename.lower().endswith('.rar'):
                # Run unrar
                cmd = (settings.UNRAR_PATH, 'x', '-y', os.path.join(self.full_path, sub_path, filename))
                (result, errors) = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()

    def get_video_list(self, sub_path=''):
        '''Returns list of subpaths to all videos in the current package, including subdirectories'''

        video_filename_list = list()

        for filename in os.listdir(os.path.join(self.full_path, sub_path)):
            # Go recursively into subdirectories
            if os.path.isdir(os.path.join(self.full_path, sub_path, filename)):
                sub_list = self.get_video_list(os.path.join(sub_path, filename))
                video_filename_list.extend(sub_list)

            # Keep a list of videos
            (file_type, file_encoding) = mimetypes.guess_type(os.path.join(self.full_path, sub_path, filename))
            if file_type is not None and file_type.startswith('video'):
                video_filename_list.append(os.path.join(sub_path, filename))

        return video_filename_list




