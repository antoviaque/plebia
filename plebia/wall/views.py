from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

from lxml.html import soupparser
from lxml.cssselect import CSSSelector

import re
import mechanize
import subprocess

from wall.models import *


def index(request):
    # Process new wall post submition
    if request.method == 'POST':
        form = PostForm(request.POST)
        post = add_new_post(form)
        return HttpResponseRedirect('/')
    else:
        form = PostForm()

    # Display lastest posts on the wall
    latest_post_list = Post.objects.all().order_by('-date_added')[:20]

    return render_to_response('wall/index.html', {
        'form': form,
        'preload': "none",
        'latest_post_list': latest_post_list,
    }, context_instance=RequestContext(request))

def add_new_post(form):
    if form.is_valid():
        # Find or create objects needed to create this post:
        # Series
        name = form.cleaned_data['name']
        series, created = Series.objects.get_or_create(name=name)
        # SeriesSeason
        season_number = form.cleaned_data['season']
        season, created = SeriesSeason.objects.get_or_create(number=season_number, series=series)
        # SeriesSeasonEpisode
        episode_number = form.cleaned_data['episode']
        episode, created = SeriesSeasonEpisode.objects.get_or_create(number=episode_number,
                season=season)

        if created:
            # Since the episode object was just created, we need to find the right torrent
            episode.torrent = get_torrent_by_episode(episode)
            episode.save()

        # And finally the Post object itself
        post = Post()
        post.episode = episode
        post.save()
        return post
    else:
        return None

def video(request, post_id):
    '''Return HTML to display when a video is getting ready (ajax)'''
    try: 
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        post = "Could not load video"

    episode = post.episode
    season = episode.season
    series = season.series
    torrent = episode.torrent
    video = episode.video

    return render_to_response('wall/video.html', {
        'post': post,
        'episode': episode,
        'season': season,
        'series': series,
        'torrent': torrent,
        'video': video,
        'preload': "auto",
    }, context_instance=RequestContext(request))


def get_torrent_by_episode(episode):
    season = episode.season
    series = season.series

    search_string = "tv %s s%02de%02d" % (series.name, season.number, episode.number)
    torrent = get_torrent_by_search(search_string)

    return torrent


def get_torrent_by_search(search_string):
    torrent = Torrent()

    br = mechanize.Browser()
    br.open("http://torrentz.eu/")

    br.select_form(nr=0)
    br["f"] = search_string
    response = br.submit()
    html_result = response.get_data()

    # First check if any torrent was found at all
    if(re.search("Could not match your exact query", html_result)):
        return None
    
    # Get the list of torrents results
    root = soupparser.fromstring(html_result)
    sel = CSSSelector(".results dl")
    element = sel(root)
    if element is None:
        return None
    else:
        # Build the torrent object
        torrent.hash = element[0].cssselect("dt a")[0].get("href")[1:]
        torrent.seeds = element[0].cssselect("dd .u")[0].text_content().translate(None, ',')
        torrent.peers = element[0].cssselect("dd .d")[0].text_content().translate(None, ',')
        if torrent.hash is None or torrent.seeds is None or torrent.seeds <= 0:
            return None
        else:
            torrent.save()
            return torrent

