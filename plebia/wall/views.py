from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from wall.models import Post, PostForm

import re
import mechanize
import subprocess

def index(request):
    # Process new wall post submition
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.torrent_hash, post.torrent_name = get_torrent(post.series_name, post.series_season, post.series_episode)
            post.save()
            return HttpResponseRedirect('/')
    else:
        form = PostForm()

    # Display lastest posts on the wall
    latest_post_list = Post.objects.all().order_by('-pub_date')[:20]

    return render_to_response('wall/index.html', {
        'form': form,
        'latest_post_list': latest_post_list,
    }, context_instance=RequestContext(request))


def get_torrent(series_name, series_season, series_episode):
    search_string = "tv %s s%02de%02d" % (series_name, series_season, series_episode)

    br = mechanize.Browser()
    br.open("http://torrentz.eu/")

    br.select_form(nr=0)
    br["f"] = search_string
    response = br.submit()
    #html_result = response.get_data()
    
    # Get the first link that gives a hash key
    for link in br.links(url_regex="/[a-z0-9]{40}"):
        return link.url[1:], link.text

    return None, None


def update_posts(request):
    latest_post_list = Post.objects.all().order_by('-pub_date')[:100]

    # Get current torrents status in deluge
    cmd = list(settings.DELUGE_COMMAND)
    cmd.append('info')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (output, errors) = p.communicate()
    torrent_list = parse_deluge_output(output)

    # Go over all posts to update their torrent info
    for post in latest_post_list:
        cmd = list(settings.DELUGE_COMMAND)
        torrent = get_torrent_by_hash(torrent_list, post.torrent_hash)

        # Start download of new torrents
        if post.torrent_status == 'New':
            cmd.append('add magnet:?xt=urn:btih:%s' % post.torrent_hash)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            (result, errors) = p.communicate()
            # FIXME Check return result
            post.torrent_status = 'Downloading'
            post.save()

        # Update status of downloading torrents
        elif post.torrent_status == 'Downloading' and torrent:
            # FIXME Check for failed torrent
            post.torrent_progress = torrent['torrent_progress']
            if torrent['torrent_name']:
                post.torrent_name = torrent['torrent_name']
                post.file_path = torrent['torrent_name'][:-4]
                post.save()
            if post.torrent_progress == 100.0:
                post.torrent_status = 'Completed'
                post.save()

                # FIXME Check for errors
                # Generate thumbnail
                subprocess.Popen(['ffmpeg', '-i', settings.DOWNLOAD_DIR + post.torrent_name, '-ss', '120', '-vframes', '1', '-r', '1', '-s', '640x360', '-f', 'image2', settings.DOWNLOAD_DIR + post.file_path + '.jpg'])
                # Convert to WebM
                subprocess.Popen(['ffmpeg', '-i', settings.DOWNLOAD_DIR + post.torrent_name, '-b', '1500k', '-acodec', 'libvorbis', '-ac', '2', '-ab', '96k', '-ar', '44100', '-s', '640x360', '-r', '18', settings.DOWNLOAD_DIR + post.file_path + '.webm'])

    return render_to_response('blank.html')


def get_torrent_by_hash(torrent_list, torrent_hash):
    for torrent in torrent_list:
        if torrent['torrent_hash'] == torrent_hash:
            return torrent
    return None


def parse_deluge_output(output):
    result_list = output.strip().split("\n \n")
    torrent_list = list()
    for result in result_list:
        torrent = dict()
        m = re.match(r"""Name: (?P<torrent_name>.+)
ID: (?P<torrent_hash>.+)
State: (?P<state>.+)
Seeds: (?P<seeds>.+)
Size: (?P<size>.+)\n?(?P<progress>.*)""", result, re.MULTILINE)
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

