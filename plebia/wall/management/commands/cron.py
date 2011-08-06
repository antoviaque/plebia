from django.core.management.base import BaseCommand, CommandError
from plebia.wall.models import Post, Video
from django.conf import settings

import re
import subprocess
import time
import os
import mimetypes

DELAY = 5

class Command(BaseCommand):
    help = 'Runs the cron tasks, every second for 1 minute'

    def handle(self, *args, **options):
        start = time.time()
        next = start
        while next <= start+50-DELAY:
            update_posts()

            next += DELAY
            time.sleep(next - time.time())


def update_posts():
    latest_post_list = Post.objects.all().order_by('-date_added')[:50]

    # Get current torrents status in deluge
    cmd = list(settings.DELUGE_COMMAND)
    cmd.append('info')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (output, errors) = p.communicate()
    torrent_list = parse_deluge_output(output)

    # Go over all posts to update their torrent info
    for post in latest_post_list:
        episode = post.episode
        torrent = episode.torrent

        cmd = list(settings.DELUGE_COMMAND)
        deluge_torrent_info = get_torrent_by_hash(torrent_list, torrent.hash)

        if torrent.status == 'New':
            start_download(torrent)

        elif torrent.status == 'Downloading' and deluge_torrent_info:
            update_download_status(episode, deluge_torrent_info)

            if torrent.progress == 100.0:
                locate_video(episode)
                start_transcoding(episode)

        elif torrent.status == 'Transcoding':
            update_transcoding_status(episode)


def start_download(torrent):
    '''Start download of new torrents'''

    cmd = list(settings.DELUGE_COMMAND)
    cmd.append('add magnet:?xt=urn:btih:%s' % torrent.hash)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (result, errors) = p.communicate()
    # FIXME Check return result
    torrent.status = 'Downloading'
    torrent.save()


def update_download_status(episode, deluge_torrent_info):
    '''Update status of downloading torrents'''

    # FIXME Check for failed torrent

    torrent = episode.torrent
    torrent.progress = deluge_torrent_info['torrent_progress']
    torrent.save()
   
    # As soon as we get the torrent name, update it
    if deluge_torrent_info['torrent_name'] and torrent.name == "":
        torrent.name = deluge_torrent_info['torrent_name']
        torrent.save()


def locate_video(episode):
    torrent = episode.torrent
    torrent_path = torrent.name

    # Check if the video has already been located for this torrent/episode
    if episode.video is not None:
        return episode.video

    video = Video()
    # If the torrent is a single file, that's the one we want
    if os.path.isfile(os.path.join(settings.DOWNLOAD_DIR, torrent_path)):
        video.original_path = torrent_path

    # If the torrent is a directory, look inside
    elif os.path.isdir(os.path.join(settings.DOWNLOAD_DIR, torrent_path)):
        video_filename_list = get_videos_from_directory(torrent_path)
        # If didn't find any video, can't create the video object
        if len(video_filename_list) == 0: 
            return None

        # Select the biggest video
        max_filename = None 
        max_size = 0
        for video_filename in video_filename_list:
            video_size = os.stat(os.path.join(settings.DOWNLOAD_DIR, video_filename))
            if video_size > max_size:
                max_filename = video_filename
                max_size = video_size

        video.original_path = max_filename

    # Save everything
    video.save()
    episode.video = video
    episode.save()


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
            print result


def get_videos_from_directory(dir_path):
    # First, extract files from archives in this directory to be able to find those files too
    extract_archives_in_directory(dir_path)

    video_filename_list = list()
    for filename_short in os.listdir(os.path.join(settings.DOWNLOAD_DIR, dir_path)):
        filename = os.path.join(dir_path, filename_short)
        print filename

        # Go recursively into subdirectories
        if os.path.isdir(os.path.join(settings.DOWNLOAD_DIR, filename)):
            sub_list = get_videos_from_directory(filename)
            video_filename_list.extend(sub_list)

        # Keep a list of videos
        (file_type, file_encoding) = mimetypes.guess_type(os.path.join(settings.DOWNLOAD_DIR, filename))
        if file_type is not None and file_type.startswith('video'):
            video_filename_list.append(filename)
            print 'VIDEO => ' + filename

    return video_filename_list


def start_transcoding(episode):
    torrent = episode.torrent
    torrent.status = 'Transcoding'
    torrent.save()

    video = episode.video
    prefix = video.original_path[:-4]
    video.webm_path = prefix + '.webm'
    video.mp4_path = prefix + '.mp4'
    video.ogv_path = prefix + '.ogv'
    video.image_path = prefix + '.jpg'
    video.save()

    # FIXME Check for errors
    # Generate thumbnail
    subprocess.Popen([settings.FFMPEG_PATH, '-i', os.path.join(settings.DOWNLOAD_DIR, video.original_path), '-ss', '120', '-vframes', '1', '-r', '1', '-s', '640x360', '-f', 'image2', settings.DOWNLOAD_DIR + video.image_path])
    # Convert to WebM
    subprocess.Popen([settings.FFMPEG_PATH, '-i', os.path.join(settings.DOWNLOAD_DIR, video.original_path), '-b', '1500k', '-acodec', 'libvorbis', '-ac', '2', '-ab', '96k', '-ar', '44100', '-s', '640x360', '-r', '18', settings.DOWNLOAD_DIR + video.webm_path])
    # Convert to OGV
    #subprocess.Popen([settings.FFMPEG2THEORA_PATH, '-p', 'pro', settings.DOWNLOAD_DIR + video.original_path])


def update_transcoding_status(episode):
    '''Check if video transcoding is over'''

    # FIXME: Need proper queue handling
    torrent = episode.torrent
    video = episode.video

    retcode = subprocess.call([settings.BIN_DIR+"check_transcoding.sh", video.original_path])
    
    if retcode: # ffmpeg process not found, transcoding over
        torrent.status = 'Completed'
        torrent.save()


def get_torrent_by_hash(torrent_list, torrent_hash):
    for torrent in torrent_list:
        if torrent['torrent_hash'] == torrent_hash:
            return torrent
    return None


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

