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
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

from wall.models import *


# Views #############################################################

def index(request):
    # Process new wall post submition
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = add_new_post(form)
            if post:
                return HttpResponseRedirect('/')
    else:
        form = PostForm()

    # Display lastest posts on the wall
    latest_post_list = Post.objects.all().order_by('-date_added')[:50]

    return render_to_response('wall/index.html', {
        'form': form,
    }, context_instance=RequestContext(request))

def ajax_search(request, search_string):
    series_list = Series.objects.filter(name__contains=search_string)[:10]
    
    return render_to_response('wall/search.html', {
        'series_list': series_list,
    }, context_instance=RequestContext(request))
    

# Helpers - Adding a post ###########################################

def add_new_post(form):
    # Find or create objects needed to create this post:
    # Series
    name = form.cleaned_data['name']
    series = Series.objects.get(name=name)

    # Make sure the series seasons & episodes are up to date
    series.update_seasons()

    # SeriesSeason
    season_number = form.cleaned_data['season']
    season = SeriesSeason.objects.get(number=season_number, series=series)
    
    # SeriesSeasonEpisode
    episode_number = form.cleaned_data['episode']
    episode = SeriesSeasonEpisode.objects.get(number=episode_number, season=season)

    # Start download of episode if needed (and of next episode, to download it while we watch)
    episode.start_download()
    episode.next_episode.start_download()

    # And finally the Post object itself
    post = Post()
    post.episode = episode
    post.save()
    return post



