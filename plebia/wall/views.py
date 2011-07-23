from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

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
        'preload': "none",
        'latest_post_list': latest_post_list,
    }, context_instance=RequestContext(request))

def post_detail(request, post_id):
    '''Send individual post attributes in JSON format (ajax)'''
    try: 
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        post = None
    data = serializers.serialize('json', [post])
    return HttpResponse(data, 'application/javascript')

def video(request, post_id):
    '''Return HTML to display when a video is getting ready (ajax)'''
    try: 
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        post = "Could not load video"
    return render_to_response('wall/video.html', {
        'post': post,
        'preload': "auto",
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


