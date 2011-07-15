from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from wall.models import Post, PostForm

import re
import mechanize
import subprocess

# FIXME Needs to be moved to config file
DELUGE_COMMAND = ['/usr/bin/deluge-console', '-u', 'localclient', '-P', '5f783e797a66d690dd6e6e008ce2cde3924e9e2f']


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
    search_string = "tv %s s%02de%02d 720p" % (series_name, series_season, series_episode)

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
    cmd = list(DELUGE_COMMAND)
    cmd.append('info')
    output = subprocess.check_output(cmd)
    torrent_list = parse_deluge_output(output)

    # Go over all posts to update their torrent info
    cmd = list(DELUGE_COMMAND)
    for post in latest_post_list:
        cmd = list(DELUGE_COMMAND)
        torrent = get_torrent_by_hash(torrent_list, post.torrent_hash)

        # Start download of new torrents
        if post.torrent_status == 'New':
            cmd.append('add magnet:?xt=urn:btih:%s' % post.torrent_hash)
            result = subprocess.check_output(cmd)
            # FIXME Check return result
            post.torrent_status = 'Downloading'
            post.save()

        # Update status of downloading torrents
        elif post.torrent_status == 'Downloading':
            # FIXME Check for failed torrent
            post.torrent_progress = torrent['torrent_progress']
            if post.torrent_progress == 100.0:
                post.torrent_status = 'Completed'
            if torrent['torrent_name']:
                post.torrent_name = torrent['torrent_name']
            post.save()

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

